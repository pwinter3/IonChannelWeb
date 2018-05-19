import json
import numpy as np
import time

from django import forms
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import escape

import icdb


PATH_DB = '/home/ubuntu/webserver/ionchannel/levin.db'
LOG_FILENAME = '/home/ubuntu/webserver/debug'


def debuglog(s):
    log_file = open(LOG_FILENAME, 'a')
    log_file.write(str(s))
    log_file.write('\n')
    log_file.close()


def get_list_of_proteins(
        curr_selected_tissues, curr_threshold_value, include_betse=True,
        specificity_option='comprehensive'):
    db = icdb.IonChannelDatabase(PATH_DB)
    protein_label_list = []
    upac_record_list = db.get_in_betse_or_expr_threshold_protein(
        curr_selected_tissues, curr_threshold_value,
        include_betse=include_betse)
    for upac_record in upac_record_list:
        upac, name, gene_symbol = upac_record
        protein_label = '%s (%s|%s)' % (name, upac, gene_symbol)
        protein_label_list.append((protein_label, upac))
    protein_label_list.sort(key=lambda x: x[0])
    return protein_label_list


class CustomMC(forms.MultipleChoiceField):
    def validate(self, value):
        pass


class db_form(forms.Form):

    def __init__(self, data=None, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(db_form, self).__init__(data, *args, **kwargs)
        curr_selected_tissues = ['adipose tissue']
        curr_threshold_value = 10.0
        include_betse = True
        tissue_options = []
        db = icdb.IonChannelDatabase(PATH_DB)
        tissue_list = db.get_tissue_names()
        for tissue_name in tissue_list:
            tissue_options.append((tissue_name, tissue_name))
        self.fields['tissue_mc'] = forms.MultipleChoiceField(
            choices=tissue_options,
            initial=curr_selected_tissues,
            widget=forms.SelectMultiple(attrs={'size':15}),
            required=True,
            label='Tissues',
            )
        self.fields['threshold'] = forms.DecimalField(
            initial=curr_threshold_value,
            max_value=1000000,
            min_value=0,
            max_digits=8,
            decimal_places=1,
            label='Threshold:',
            )
        self.fields['include_betse'] = forms.BooleanField(
            initial=include_betse,
            label='Include BETSE ion channels?',
            required=False
            )
        protein_options = []
        protein_labels = get_list_of_proteins(
            curr_selected_tissues, curr_threshold_value,
            include_betse=include_betse)
        protein_upac_list = []
        for protein_label in protein_labels:
            protein_upac = protein_label[1]
            long_name = protein_label[0]
            protein_options.append((protein_upac, long_name))
            protein_upac_list.append(protein_upac)
        self.fields['protein_mc'] = CustomMC(
            choices=protein_options,
            widget=forms.SelectMultiple(attrs={'size':15}),
            required=True,
            label='Ion Channels',
            )
        self.fields['channel_select_type'] = forms.ChoiceField(
            choices=[('comp', 'Comprehensive'), ('uniq', 'Unique')],
            initial='comp',
            widget=forms.RadioSelect(attrs={'disabled':'disabled'}),
            label='Ion channel selection type:',
            )
        self.fields['protein_desc'] = forms.CharField(
            widget=forms.Textarea(attrs={
                'rows':12, 'cols':30, 'readonly':True, 'style':'resize:none'}),
            label=get_protein_desc(protein_upac_list),
            required=False
            )
        self.fields['lookup_button'] = forms.CharField(
            widget=forms.Textarea(attrs={
                'rows':15, 'cols':30, 'readonly':True}),
            label=get_protein_desc(protein_upac_list),
            required=False
            )

    def clean(self):
        cleaned_data = super(forms.Form, self).clean()
        t1 = cleaned_data.get("tissue_mc", None)
        t2 = cleaned_data.get("threshold", None)
        return cleaned_data


def make_compound_list(interaction_id_list, db):
    comp_inter_dict = {}
    for interaction_id in interaction_id_list:
        interaction_record = db.lookup_interaction(interaction_id)
        compound_id = interaction_record['CompoundId']
        if not compound_id in comp_inter_dict:
            comp_inter_dict[compound_id] = []
        param_value = interaction_record['AssayValue']
        try: 
            param_value = float(param_value)
            comp_inter_dict[compound_id].append(param_value)
        except:
            comp_inter_dict[compound_id].append(None)
    stat_dict = {}
    for compound_id, param_values in comp_inter_dict.iteritems():
        param_value_array = np.array(param_values, dtype=np.float)
        param_value_min = np.amin(param_value_array)
        param_value_max = np.amax(param_value_array)
        param_value_avg = param_value_array.mean()
        stat_dict[compound_id] = (
            param_value_min, param_value_avg, param_value_max)
    compound_sorted_list = []
    for compound_id in stat_dict.keys():
        compound_sorted_list.append(compound_id)
    def cmp(a, b):
        if stat_dict[a][0] < stat_dict[b][0]:
            return -1
        elif stat_dict[a][0] > stat_dict[b][0]:
            return 1
        else:
            if stat_dict[a][1] < stat_dict[b][1]:
                return -1
            elif stat_dict[a][1] > stat_dict[b][1]:
                return 1
            else:
                return 0
    compound_sorted_list.sort(cmp)
    return compound_sorted_list, stat_dict


def index(request):
    new_request = HttpRequest()
    form = db_form(request=new_request)
    return render(request, 'levindb/db.html', {'form': form})


def load_proteins(request):
    datadict = json.loads(request.body)
    curr_selected_tissues = datadict['tissues']
    curr_threshold_value = float(datadict['threshold'])
    include_betse = datadict['include_betse']
    protein_options = []
    protein_labels = get_list_of_proteins(
        curr_selected_tissues, curr_threshold_value,
        include_betse=include_betse)
    for protein_label in protein_labels:
        long_name, protein_upac = protein_label
        protein_options.append({'upac':protein_upac, 'label':long_name})
    return HttpResponse(json.dumps(protein_options),
        content_type="application/json")


def get_protein_desc(upac_list):
    protein_desc_list = []
    db = icdb.IonChannelDatabase(PATH_DB)
    for upac in upac_list:
        protein_record = db.lookup_protein(upac)
        gene_symbol = protein_record['GeneSymbol']
        name = protein_record['Name']
        ion_channel_sub_class = protein_record['IonChannelSubClass']
        channelpedia_info_record = db.get_channelpedia_info(
            ion_channel_sub_class)
        if channelpedia_info_record is not None:
            protein_desc = channelpedia_info_record['ChannelpediaText']
        else:
            protein_desc = ''
        protein_desc_list.append(
            (upac, gene_symbol, name, ion_channel_sub_class, protein_desc))
    return protein_desc_list

def load_protein_desc(request):
    datadict = json.loads(request.body)
    upac_list = datadict['protein_upacs']
    return_data = []
    protein_desc_list = get_protein_desc(upac_list)
    for record in protein_desc_list:
        upac, gene_symbol, name, ion_channel_sub_class, protein_desc = record
        if ion_channel_sub_class == '':
            ion_channel_sub_class == 'No ion channel class available'
        if protein_desc == '':
            protein_desc = '(No description available)'
        return_data.append(
            {'upac':upac,
            'gene_symbol':gene_symbol,
            'name':name,
            'ion_channel_sub_class':ion_channel_sub_class,
            'protein_desc':protein_desc})
    return HttpResponse(
        json.dumps(return_data), content_type="application/json")

def make_results_table(request):
    datadict = json.loads(request.body)
    tissue_selection = datadict['tissues']
    tissue_selection.sort()
    protein_selection = datadict['proteins']
    db = icdb.IonChannelDatabase(PATH_DB)
    protein_label_dict = {}
    for upac in protein_selection:
        protein_record = db.lookup_protein(upac)
        gene_symbol = protein_record['GeneSymbol']
        name = protein_record['Name']
        in_betse = protein_record['InBETSE']
        ion_channel_sub_class = protein_record['IonChannelSubClass']
        channelpedia_record = db.get_channelpedia_info(ion_channel_sub_class)
        if channelpedia_record is not None:
            protein_desc = channelpedia_record['ChannelpediaText']
            url = channelpedia_record['ChannelpediaURL']
        else:
            protein_desc = ''
            url = ''
        protein_label = (upac, gene_symbol, name, in_betse, protein_desc, url)
        protein_label_dict[upac] = protein_label   
    final_results = []
    for tissue_name in tissue_selection:
        for upac in protein_selection:
            upac, gene_symbol, name, in_betse, desc, url = \
                protein_label_dict[upac]
            specificity_score = db.get_specificity(tissue_name, upac)
            if specificity_score is not None:
                protein_specificity = '%.2f' % (float(specificity_score),)
            else:
                protein_specificity = 'N/A'
            expr_level_list = \
                db.get_expression_level_by_uniprot_accnum_tissue_dataset(
                    upac, tissue_name, 'hpa')
            if expr_level_list:
                expr_level = '%.2f' % expr_level_list[0]
            else:
                expr_level = 'N/A'
            expr_level_qual_list = \
                db.get_expression_level_qual_by_uniprot_accnum_tissue_dataset(
                    upac, tissue_name, 'hpa')
            if expr_level_qual_list:
                expr_level_qual = '%s' % expr_level_qual_list[0]
            else:
                expr_level_qual = 'N/A'
            try:
                interaction_id_list = db.get_interaction_ids_by_uniprot_accnum(
                    upac, type='IC50', unit='nM')
            except Exception as e:
                interaction_id_list = []
            if interaction_id_list:
                compound_sorted_list, stat_dict = \
                    make_compound_list(interaction_id_list, db)
                for compound_id in compound_sorted_list:
                    compound_record = db.lookup_compound(compound_id)
                    compound_name = compound_record['Name']
                    compound_chemblid = compound_record['ChemblId']
                    BASE_URL = 'https://www.ebi.ac.uk/chembl/compound/inspect/'
                    if compound_name != '':
                        compound_label = '%s (%s)' % (
                            compound_name, compound_chemblid)
                    else:
                        compound_label = compound_chemblid
                    compound_label = '<a HREF="%s/%s">%s</a>' % (
                        BASE_URL, escape(compound_chemblid),
                        escape(compound_label))
                    min, avg, max = stat_dict[compound_id]
                    param_value = '%.2f - %.2f' % (min, max)
                    final_results.append([
                        escape(tissue_name), escape(upac), escape(gene_symbol),
                        escape(name), escape(expr_level),
                        escape(expr_level_qual), escape(protein_specificity),
                        escape(in_betse), compound_label, escape(param_value)])
            else:
                final_results.append([escape(tissue_name), escape(upac),
                    escape(gene_symbol), escape(name), escape(expr_level),
                    escape(expr_level_qual), escape(protein_specificity),
                    escape(in_betse), escape('No interacting compounds'),
                    escape('N/A')])
    result_header_str = '<table border="1">'
    result_header_str += '<col width="130">'
    result_header_str += '<col width="80">'
    result_header_str += '<col width="80">'
    result_header_str += '<col width="260">'
    result_header_str += '<col width="90">'
    result_header_str += '<col width="90">'
    result_header_str += '<col width="90">'
    result_header_str += '<col width="70">'
    result_header_str += '<col width="260">'
    result_header_str += '<col width="60">'
    result_header_str += '\n'
    result_header_str += '<tr>'
    result_header_str += '<th>Tissue</th>'
    result_header_str += '<th>Ion channel UniProtKB AC</th>'
    result_header_str += '<th>Ion channel gene symbol</th>'
    result_header_str += '<th>Ion channel name</th>'
    result_header_str += '<th>Gene expression (RNA)</th>'
    result_header_str += '<th>Gene expression (Protein)</th>'
    result_header_str += '<th>Protein specificity</th>'
    result_header_str += '<th>In BETSE?</th>'
    result_header_str += '<th>Interacting compound</th>'
    result_header_str += '<th>IC50 Values (nM) <br/> (Min - Max)</th>'
    result_header_str += '</tr>'
    result_header_str += '</table>'
    result_str = '<table border="1">'
    result_str += '<col width="130">'
    result_str += '<col width="80">'
    result_str += '<col width="80">'
    result_str += '<col width="260">'
    result_str += '<col width="90">'
    result_str += '<col width="90">'
    result_str += '<col width="90">'
    result_str += '<col width="70">'
    result_str += '<col width="260">'
    result_str += '<col width="60">'
    result_str += '\n'
    result_str += '<tr><th>Tissue</th>'
    result_str += '<th>Ion channel UniProtKB AC</th>'
    result_str += '<th>Ion channel gene symbol</th>'
    result_str += '<th>Ion channel name</th>'
    result_str += '<th>Gene expression (RNA)</th>'
    result_str += '<th>Gene expression (Protein)</th>'
    result_str += '<th>Protein specificity</th>'
    result_str += '<th>In BETSE?</th>'
    result_str += '<th>Interacting compound</th>'
    result_str += '<th>IC50 Values (nM) <br/> (Min - Max)</th></tr>'
    for data_record in final_results:
        result_str += '<tr>'
        result_str += '<td align="center">%s</td>\n' % data_record[0]
        result_str += '<td align="center">%s</td>\n' % data_record[1]
        result_str += '<td align="center">%s</td>\n' % data_record[2]
        result_str += '<td align="center">%s</td>\n' % data_record[3]
        result_str += '<td align="center">%s</td>\n' % data_record[4]
        result_str += '<td align="center">%s</td>\n' % data_record[5]
        result_str += '<td align="center">%s</td>\n' % data_record[6]
        result_str += '<td align="center">%s</td>\n' % data_record[7]
        result_str += '<td align="center">%s</td>\n' % data_record[8]
        result_str += '<td align="center">%s</td>\n' % data_record[9]
        result_str += '</tr>'
    result_str += '</table>\n'
    result_str += '<br/><br/><a href="%s">Back</a>' % request.get_full_path()
    result_dict = {}
    result_dict['results_table_header'] = result_header_str
    result_dict['results_table'] = result_str
    return HttpResponse(json.dumps(result_dict),
        content_type="application/json")

