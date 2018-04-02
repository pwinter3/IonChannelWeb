from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpRequest
from django.template import loader
from django.shortcuts import render
from django import forms
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from .models import *
from .levindb_p import *
import json
import logging
import time
import numpy as np

PATH_DB = '/home/ubuntu/webserver/ionchannel/levin.db'
LOG_FILENAME = '/home/ubuntu/webserver/debug'

def debuglog(s):
    log_file = open(LOG_FILENAME, 'a')
    log_file.write(str(s))
    log_file.write('\n')
    log_file.close()

class CustomMC(forms.MultipleChoiceField):
    def validate(self, value):
        pass

def get_list_of_tissues():
    tissue_exclusion_list = [
        u'B-lymphocyte',
        u'DAUDI cell',
        u'HL-60 cell',
        u'K-562 cell',
        u'Leydig cell',
        u'MOLT-4 cell',
        u'RAJI cell',
        u'adipocyte',
        u'adrenal cortex',
        u'amygdala',
        u'atrioventricular node',
        u'basis pedunculi cerebri',
        u'blood',
        u'brain',
        u'bronchial epithelial cell',
        u'cardiac muscle fiber',
        u'caudate nucleus',
        u'cerebellum',
        u'cingulate cortex',
        u'colorectal adenocarcinoma cell',
        u'culture condition:CD34+ cell',
        u'culture condition:CD4+ cell',
        u'culture condition:CD56+ cell',
        u'culture condition:CD8+ cell',
        u'dendritic cell',
        u'endothelial cell',
        u'erythroid progenitor cell',
        u'germ cell',
        u'globus pallidus',
        u'heart',
        u'hypophysis',
        u'hypothalamus',
        u'interstitial cell',
        u'lymphoblast',
        u'medulla oblongata',
        u'monocyte',
        u'nasal nerve',
        u'occipital lobe',
        u'olfactory bulb',
        u'pancreatic islet',
        u'parietal lobe',
        u'pineal gland',
        u'pons',
        u'prefrontal cortex',
        u'retina',
        u'seminiferous tubule',
        u'spinal cord',
        u'spinal ganglion',
        u'subthalamic nucleus',
        u'superior cervical ganglion',
        u'temporal lobe',
        u'thalamus',
        u'thymus',
        u'tongue',
        u'trachea',
        u'trigeminal ganglion',
        u'uterine cervix',
        u'uterus',
        ]
    db_obj = LevinDatabase(PATH_DB)
    filtered_tissue_name_list = []
    tissue_name_record_list = db_obj.get_all_tissue_names()
    for tissue_name_record in tissue_name_record_list:
        tissue_name = tissue_name_record[0]
        if not tissue_name in tissue_exclusion_list:
            filtered_tissue_name_list.append(tissue_name)
    db_obj.cleanup()
    return filtered_tissue_name_list

def get_list_of_proteins(curr_selected_tissues, curr_threshold_value,
        include_betse=True, specificity_option='comprehensive'):
    db_obj = LevinDatabase(PATH_DB)
    curr_threshold_value = float(curr_threshold_value)
    protein_labels = []
    upac_record_list = db_obj.get_in_betse_or_expr_threshold_protein(
            curr_selected_tissues, curr_threshold_value,
            include_betse=include_betse)
    for upac_record in upac_record_list:
        upac, name, gene_symbol = upac_record
        protein_label = '%s (%s|%s)' % (name, upac, gene_symbol)
        protein_labels.append((protein_label, upac))
    protein_labels.sort(key=lambda x: x[0])
    db_obj.cleanup()
    return protein_labels

class db_form(forms.Form):

    def __init__(self, data=None, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(db_form, self).__init__(data, *args, **kwargs)
        cst = ['adipose tissue',]
        ctv = 10.0
        include_betse = True
        tissue_options = []
        tissue_list = get_list_of_tissues()
        for tissue_name in tissue_list:
            tissue_options.append((tissue_name, tissue_name))
        self.fields['tissue_mc'] = forms.MultipleChoiceField(
            choices=tissue_options,
            initial=cst,
            widget=forms.SelectMultiple(attrs={'size': 15}),
            required=True,
            label='Tissues',
            )
        self.fields['threshold'] = forms.DecimalField(
            initial=ctv,
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
        protein_labels = get_list_of_proteins(cst, ctv, 
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
            widget=forms.Textarea(attrs={'rows':15, 'cols':60,
                    'readonly':True}),
            label=get_protein_desc(protein_upac_list),
            required=False
            )
        self.fields['lookup_button'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows':15, 'cols':60,
                    'readonly':True}),
            label=get_protein_desc(protein_upac_list),
            required=False
            )

    def clean(self):
        cleaned_data = super(forms.Form, self).clean()
        t1 = cleaned_data.get("tissue_mc", None)
        t2 = cleaned_data.get("threshold", None)
        return cleaned_data

def make_compound_list(interaction_id_record_list, db_obj):
    comp_inter_dict = {}
    for interaction_id_record in interaction_id_record_list:
        interaction_id = interaction_id_record[0]
        interaction_record = db_obj.lookup_interaction(interaction_id)
        compound_id = interaction_record[2]
        if not compound_id in comp_inter_dict:
            comp_inter_dict[compound_id] = []
        param_value = interaction_record[5]
        try: 
            param_value = float(param_value)
            comp_inter_dict[compound_id].append(param_value)
        except:
            comp_inter_dict[compound_id].append(None)
    comp_inter_min_avg_max_dict = {}
    for compound_id, param_values in comp_inter_dict.iteritems():
        param_value_array = np.array(param_values, dtype=np.float)
        param_value_min = np.amin(param_value_array)
        param_value_max = np.amax(param_value_array)
        param_value_avg = param_value_array.mean()
        comp_inter_min_avg_max_dict[compound_id] = (param_value_min, param_value_avg, param_value_max)
    compound_sorted_list = []
    for compound_id in comp_inter_min_avg_max_dict.keys():
        compound_sorted_list.append(compound_id)
    def cmp(a, b):
        if comp_inter_min_avg_max_dict[a][0] < comp_inter_min_avg_max_dict[b][0]:
            return -1
        elif comp_inter_min_avg_max_dict[a][0] > comp_inter_min_avg_max_dict[b][0]:
            return 1
        else:
            if comp_inter_min_avg_max_dict[a][1] < comp_inter_min_avg_max_dict[b][1]:
                return -1
            elif comp_inter_min_avg_max_dict[a][1] > comp_inter_min_avg_max_dict[b][1]:
                return 1
            else:
                return 0
    compound_sorted_list.sort(cmp)
    return compound_sorted_list, comp_inter_min_avg_max_dict

def index(request):
    if request.method == 'POST':
        form = db_form(request.POST)
        debuglog('Checking if form is valid')
        if form.is_valid():
            debuglog('Form is valid')
            db_obj = LevinDatabase(PATH_DB)
            myresults = form.cleaned_data
            tissue_selection = myresults['tissue_mc']
            tissue_selection.sort()
            protein_selection = myresults['protein_mc']
            protein_label_dict = {}
            for upac in protein_selection:
                protein_record = db_obj.lookup_protein(upac)
                gene_symbol = protein_record[1]
                name = protein_record[2]
                in_betse = protein_record[6]
                ion_channel_sub_class = protein_record[8]
                channelpedia_record = db_obj.get_channelpedia_info(ion_channel_sub_class)
                desc = channelpedia_record[0]
                if desc == '':
                    desc = 'N/A'
                url = channelpedia_record[1]
                protein_label = (upac, gene_symbol, name, in_betse, desc, url)
                protein_label_dict[upac] = protein_label          
            final_results = []
            for tissue_name in tissue_selection:
                for upac in protein_selection:
                    upac, gene_symbol, name, in_betse, desc, url = protein_label_dict[upac]
                    protein_specificity = db_obj.get_specificity(tissue_name, upac)
                    if protein_specificity != '':
                        protein_specificity = '%.2f' % (float(db_obj.get_specificity(tissue_name, upac)),)
                    expr_level_record_list = db_obj.get_expr_level_for_dataset(upac, tissue_name, 'hpa')
                    if len(expr_level_record_list) > 0:
                        expr_level = '%.2f' % expr_level_record_list[0][0]
                    else:
                        expr_level = 'N/A'
                    expr_level_qual_record_list = db_obj.get_expr_level_qual_for_dataset(upac, tissue_name, 'hpa')
                    if len(expr_level_qual_record_list) > 0:
                        expr_level_qual = '%s' % expr_level_qual_record_list[0][0]
                    else:
                        expr_level_qual = 'N/A'
                    interaction_id_record_list = db_obj.get_interaction_ids_by_uniprot(upac, type='IC50', unit='nM')
                    if len(interaction_id_record_list) > 0:
                        compound_sorted_list, comp_inter_min_avg_max_dict = make_compound_list(interaction_id_record_list, db_obj)
                        for compound_id in compound_sorted_list:
                            compound_record = db_obj.lookup_compound(compound_id)
                            compound_name = compound_record[3]
                            compound_chemblid = compound_record[4]
                            BASE_URL = 'https://www.ebi.ac.uk/chembl/compound/inspect/'
                            if compound_name != '':
                                compound_label = '%s (%s)' % (compound_name, compound_chemblid)
                            else:
                                compound_label = compound_chemblid
                            compound_label = '<a HREF="%s/%s">%s</a>' % (BASE_URL, escape(compound_chemblid), escape(compound_label))
                            min, avg, max = comp_inter_min_avg_max_dict[compound_id]
                            param_value = '%.2f - %.2f' % (min, max)
                            final_results.append([escape(tissue_name), escape(upac), escape(gene_symbol), escape(name), escape(expr_level), escape(expr_level_qual), escape(protein_specificity), escape(in_betse), compound_label, escape(param_value)])
                    else:
                        final_results.append([escape(tissue_name), escape(upac), escape(gene_symbol), escape(name), escape(expr_level), escape(expr_level_qual), escape(protein_specificity), escape(in_betse), escape('No interacting compounds'), escape('N/A')])
            result_str = '<table border="1"><col width="130"><col width="80"><col width="80"><col width="260"><col width="90"><col width="90"><col width="90"><col width="70"><col width="260"><col width="60">\n'
            result_str += '<tr><th>Tissue</th>' + \
                '<th>Ion channel UniProtKB AC</th>' + \
                '<th>Ion channel gene symbol</th>' + \
                '<th>Ion channel name</th>' + \
                '<th>Gene expression (RNA)</th>' + \
                '<th>Gene expression (Protein)</th>' + \
                '<th>Protein specificity</th>' + \
                '<th>In BETSE?</th>' + \
                '<th>Interacting compound</th>' + \
                '<th>IC50 Values (nM) <br/> (Min - Max)</th></tr>'
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
            db_obj.cleanup()
            return render(request, 'levindb/results.html', {'message': result_str})
    else:
        new_request = HttpRequest()
        form = db_form(request=new_request)
        render(new_request, 'levindb/db.html', {'form': form})
    return render(request, 'levindb/db.html', {'form': form})

def load_proteins(request):
    datadict = json.loads(request.body)
    tissue_list = datadict['tissues']
    threshold = float(datadict['threshold'])
    protein_options = []
    protein_labels = get_list_of_proteins(tissue_list, threshold,
            include_betse=datadict['include_betse'])
    for protein_label in protein_labels:
        protein_upac = protein_label[1]
        long_name = protein_label[0]
        protein_options.append({'upac':protein_upac, 'label':long_name})
    return HttpResponse(json.dumps(protein_options),
            content_type="application/json")

def get_protein_desc(upac_list):
    protein_desc_list = []
    db_obj = LevinDatabase(PATH_DB)
    for upac in upac_list:
        protein_record = db_obj.lookup_protein(upac)
        gene_symbol = protein_record[1]
        name = protein_record[2]
        ion_channel_sub_class = protein_record[8]
        channelpedia_info_record = \
                db_obj.get_channelpedia_info(ion_channel_sub_class)
        protein_desc = channelpedia_info_record[0]
        protein_desc_list.append((upac, gene_symbol, name,
                ion_channel_sub_class, protein_desc))
    db_obj.cleanup()
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
        return_data.append({'upac':upac, 'gene_symbol':gene_symbol,
                'name':name, 'ion_channel_sub_class':ion_channel_sub_class,
                'protein_desc':protein_desc})
    return HttpResponse(json.dumps(return_data),
            content_type="application/json")

def make_results_table(request):
    datadict = json.loads(request.body)
    tissue_selection = datadict['tissues']
    tissue_selection.sort()
    protein_selection = datadict['proteins']
    db_obj = LevinDatabase(PATH_DB)
    protein_label_dict = {}
    for upac in protein_selection:
        protein_record = db_obj.lookup_protein(upac)
        gene_symbol = protein_record[1]
        name = protein_record[2]
        in_betse = protein_record[6]
        ion_channel_sub_class = protein_record[8]
        channelpedia_record = db_obj.get_channelpedia_info(ion_channel_sub_class)
        desc = channelpedia_record[0]
        if desc == '':
            desc = 'N/A'
        url = channelpedia_record[1]
        protein_label = (upac, gene_symbol, name, in_betse, desc, url)
        protein_label_dict[upac] = protein_label          
    final_results = []
    for tissue_name in tissue_selection:
        for upac in protein_selection:
            upac, gene_symbol, name, in_betse, desc, url = protein_label_dict[upac]
            protein_specificity = db_obj.get_specificity(tissue_name, upac)
            if protein_specificity != '':
                protein_specificity = '%.2f' % (float(db_obj.get_specificity(tissue_name, upac)),)
            expr_level_record_list = db_obj.get_expr_level_for_dataset(upac, tissue_name, 'hpa')
            if len(expr_level_record_list) > 0:
                expr_level = '%.2f' % expr_level_record_list[0][0]
            else:
                expr_level = 'N/A'
            expr_level_qual_record_list = db_obj.get_expr_level_qual_for_dataset(upac, tissue_name, 'hpa')
            if len(expr_level_qual_record_list) > 0:
                expr_level_qual = '%s' % expr_level_qual_record_list[0][0]
            else:
                expr_level_qual = 'N/A'
            interaction_id_record_list = db_obj.get_interaction_ids_by_uniprot(upac, type='IC50', unit='nM')
            if len(interaction_id_record_list) > 0:
                compound_sorted_list, comp_inter_min_avg_max_dict = make_compound_list(interaction_id_record_list, db_obj)
                for compound_id in compound_sorted_list:
                    compound_record = db_obj.lookup_compound(compound_id)
                    compound_name = compound_record[3]
                    compound_chemblid = compound_record[4]
                    BASE_URL = 'https://www.ebi.ac.uk/chembl/compound/inspect/'
                    if compound_name != '':
                        compound_label = '%s (%s)' % (compound_name, compound_chemblid)
                    else:
                        compound_label = compound_chemblid
                    compound_label = '<a HREF="%s/%s">%s</a>' % (BASE_URL, escape(compound_chemblid), escape(compound_label))
                    min, avg, max = comp_inter_min_avg_max_dict[compound_id]
                    param_value = '%.2f - %.2f' % (min, max)
                    final_results.append([escape(tissue_name), escape(upac), escape(gene_symbol), escape(name), escape(expr_level), escape(expr_level_qual), escape(protein_specificity), escape(in_betse), compound_label, escape(param_value)])
            else:
                final_results.append([escape(tissue_name), escape(upac), escape(gene_symbol), escape(name), escape(expr_level), escape(expr_level_qual), escape(protein_specificity), escape(in_betse), escape('No interacting compounds'), escape('N/A')])
    result_str = '<table border="1"><col width="130"><col width="80"><col width="80"><col width="260"><col width="90"><col width="90"><col width="90"><col width="70"><col width="260"><col width="60">\n'
    result_str += '<tr><th>Tissue</th>' + \
        '<th>Ion channel UniProtKB AC</th>' + \
        '<th>Ion channel gene symbol</th>' + \
        '<th>Ion channel name</th>' + \
        '<th>Gene expression (RNA)</th>' + \
        '<th>Gene expression (Protein)</th>' + \
        '<th>Protein specificity</th>' + \
        '<th>In BETSE?</th>' + \
        '<th>Interacting compound</th>' + \
        '<th>IC50 Values (nM) <br/> (Min - Max)</th></tr>'
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
    db_obj.cleanup()
    return HttpResponse(json.dumps(result_str), content_type="application/json")
