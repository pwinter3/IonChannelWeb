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
from .levindb import *
import json


PATH_DB = '/home/ubuntu/webserver/ionchannel/levin.db'


def debuglog(s):
    log_file = open('/home/ubuntu/webserver/debug', 'a')
    log_file.write(str(s))
    log_file.write('\n')
    log_file.close()


class CustomMC(forms.MultipleChoiceField):
    def validate(self, value):
        pass

def get_list_of_tissues():
    tissue_exclusion_list = [
        'B-lymphocyte',
        'DAUDI cell',
        'HL-60 cell',
        'K-562 cell',
        'Leydig cell',
        'MOLT-4 cell',
        'RAJI cell',
        'adipocyte',
        'adrenal cortex',
        'amygdala',
        'atrioventricular node',
        'basis pedunculi cerebri',
        'blood',
        'brain',
        'bronchial epithelial cell',
        'cardiac muscle fiber',
        'caudate nucleus',
        'cerebellum',
        'cingulate cortex',
        'colorectal adenocarcinoma cell',
        'culture condition:CD34+ cell',
        'culture condition:CD4+ cell',
        'culture condition:CD56+ cell',
        'culture condition:CD8+ cell',
        'dendritic cell',
        'endothelial cell',
        'erythroid progenitor cell',
        'germ cell',
        'globus pallidus',
        'heart',
        'hypophysis',
        'hypothalamus',
        'interstitial cell',
        'lymphoblast',
        'medulla oblongata',
        'monocyte',
        'nasal nerve',
        'occipital lobe',
        'olfactory bulb',
        'pancreatic islet',
        'parietal lobe',
        'pineal gland',
        'pons',
        'prefrontal cortex',
        'retina',
        'seminiferous tubule',
        'spinal cord',
        'spinal ganglion',
        'subthalamic nucleus',
        'superior cervical ganglion',
        'temporal lobe',
        'thalamus',
        'thymus',
        'tongue',
        'trachea',
        'trigeminal ganglion',
        'uterine cervix',
        'uterus',
    ]
    filtered_tissue_name_list = []
    #tissue_list = Tissue.objects.order_by('name')
    tissue_name_record_list = get_all_tissue_names()
    for tissue_name_record in tissue_name_record_list:
        tissue_name = tissue_name_record[0]
        if not tissue_name in tissue_exclusion_list:
            filtered_tissue_name_list.append(tissue_name)
    return filtered_tissue_name_list

# Union of tissues instead of intersection
#def get_list_of_proteins(curr_selected_tissues, curr_threshold_value):
#    curr_threshold_value = float(curr_threshold_value)
#    protein_labels = []
#    protein_list = Protein.objects.all()
#    for protein in protein_list:
#        protein_label = '%s (%s)' % (protein.uniprotaccnum, protein.genesymbol)
#        q = Expression.objects.filter(proteinuniprotaccnum=protein.uniprotaccnum).filter(sourcedbname='hpa')
#        if len(q) <= 0:
#            continue
#        expr_meets_threshold = False
#        for expr_rec in q:
#            if expr_rec.tissuename in curr_selected_tissues:
#                expr_level = float(expr_rec.exprlevel)
#                if expr_level > curr_threshold_value:
#                    expr_meets_threshold = True
#        if expr_meets_threshold and not protein_label in protein_labels:
#            protein_labels.append(protein_label)
#    protein_labels.sort()
#    return protein_labels

#def get_list_of_proteins(curr_selected_tissues, curr_threshold_value):
#    curr_threshold_value = float(curr_threshold_value)
#    protein_labels = []
#    #protein_list = Protein.objects.all()
#    upac_record_list = get_all_protein_uniprots()
#    for upac_record in upac_record_list:
#        upac = upac_record[0]
#        gene_symbol = get_gene_symbol_by_uniprot(upac)
#        protein_label = '%s (%s)' % (upac, gene_symbol)
#        #q = Expression.objects.filter(proteinuniprotaccnum=protein.uniprotaccnum).filter(sourcedbname='hpa')
#        expr_id_record_list = get_expr_ids_by_uniprot(upac)
#        if len(expr_id_record_list) == 0:
#            continue
#        expr_meets_threshold = False
#        expr_threshold_target = len(curr_selected_tissues)
#        expr_threshold_count = 0
#        for curr_tissue_name in curr_selected_tissues:
#            for expr_id_record in expr_id_record_list:
#                expr_id = expr_id_record[0]
#                expr_record = lookup_expr(expr_id)
#                dataset_name = expr_record[6]
#                if dataset_name == 'hpa':
#                    expr_tissue_name = expr_record[1]
#                    if expr_tissue_name == curr_tissue_name:
#                        expr_level = float(expr_record[3])
#                        if expr_level > curr_threshold_value:
#                            expr_threshold_count += 1
#        if expr_threshold_count == expr_threshold_target and not protein_label in protein_labels:
#            protein_labels.append(protein_label)
#    protein_labels.sort()
#    return protein_labels

def get_list_of_proteins(curr_selected_tissues, curr_threshold_value):
    curr_threshold_value = float(curr_threshold_value)
    protein_labels = []
    #protein_list = Protein.objects.all()
    upac_record_list = get_all_protein_uniprots()
    for upac_record in upac_record_list:
        upac = upac_record[0]
        gene_symbol = get_gene_symbol_by_uniprot(upac)
        protein_label = '%s (%s)' % (upac, gene_symbol)        
        expr_meets_threshold = False
        for curr_tissue_name in curr_selected_tissues:
            if exists_expr_threshold(curr_tissue_name, upac, curr_threshold_value, 'hpa'):
                expr_meets_threshold = True
                break
        protein_record = lookup_protein(upac)
        in_betse = protein_record[6]
        if not protein_label in protein_labels and (in_betse == 'Y' or expr_meets_threshold):
        #if not protein_label in protein_labels and in_betse == 'Y':
            protein_labels.append(protein_label)
    protein_labels.sort()
    return protein_labels


class db_form(forms.Form):

    def __init__(self, data=None, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(db_form, self).__init__(data, *args, **kwargs)
        cst = ['adipose tissue',]
        ctv = 10.0
        tissue_options = []
        tissue_list = get_list_of_tissues()
        for tissue_name in tissue_list:
            tissue_options.append((tissue_name, tissue_name))
        protein_options = []
        protein_labels = get_list_of_proteins(cst, ctv)
        for protein_label in protein_labels:
            protein_upac = protein_label.split()[0].strip()
            protein_options.append((protein_upac, protein_label))
        self.fields['tissue_mc'] = forms.MultipleChoiceField(
            choices=tissue_options,
            initial=cst,
            widget=forms.SelectMultiple(attrs={'size': 50}),
            required=True,
            label='Tissues',
        )
        self.fields['protein_mc'] = CustomMC(
            choices=protein_options,
            widget=forms.SelectMultiple(attrs={'size':50}),
            required=True,
            label='Ion Channels',
        )
        self.fields['threshold'] = forms.DecimalField(
            initial=ctv,
            max_value=1000000,
            min_value=0,
            max_digits=8,
            decimal_places=1,
        )
        self.fields['channel_select_type'] = forms.ChoiceField(
            choices = [('comp', 'Comprehensive'), ('uniq', 'Unique')],
            initial = 'comp',
            widget=forms.RadioSelect(),
            label = 'Ion channel selection type:',
        )
        if data:
            cst = data.get('tissue_mc', None)
            ctv = float(data.get('threshold', None))
            protein_options = []
            protein_labels = get_list_of_proteins(cst, ctv)
            for protein_label in protein_labels:
                protein_upac = protein_label.split()[0].strip()
                protein_options.append((protein_upac, protein_label))
            self.fields['protein_mc'].choices = protein_options

    def clean(self):
        cleaned_data = super(forms.Form, self).clean()
        t1 = cleaned_data.get("tissue_mc", None)
        t2 = cleaned_data.get("threshold", None)
        return cleaned_data


def index(request):
    if request.method == 'POST':
        form = db_form(request.POST)
        if form.is_valid():
            myresults = form.cleaned_data
            tissue_selection = myresults['tissue_mc']
            tissue_selection.sort()
            protein_selection = myresults['protein_mc']
            protein_label_list = []
            protein_label_dict = {}
            for upac in protein_selection:
                #protein = Protein.objects.get(uniprotaccnum=upac)
                protein_record = lookup_protein(upac)
                ic_subclass = protein_record[8]
                gene_symbol = protein_record[1]
                protein_label = '%s (%s)' % (upac, gene_symbol)
                protein_label_list.append(protein_label)
                protein_label_dict[protein_label] = upac          
            protein_label_list.sort()
            final_results = []
            for tissue_name in tissue_selection:
                for protein_label in protein_label_list:
                    upac = protein_label_dict[protein_label]
                    
                    protein_record = lookup_protein(upac)
                    in_betse = protein_record[6]

                    #expression_level_qs = Expression.objects.filter(tissuename=tissue_name).filter(proteinuniprotaccnum=upac)
                    expr_level_record_list = get_expr_level_for_dataset(upac, tissue_name, 'hpa')
                    if len(expr_level_record_list) > 0:
                        expr_level = '%.2f' % expr_level_record_list[0][0]
                    else:
                        expr_level = '0.00'
                    #interaction_qs = Interaction.objects.filter(targetuniprotaccnum=upac)
                    interaction_id_record_list = get_interaction_ids_by_uniprot(upac)
                    if len(interaction_id_record_list) > 0:
                    
                        # Need to average interactions values over each compound
                        # Not sure how to combine different assay types and parameter types, ignoring for now
                        comp_inter_dict = {}
                        for interaction_id_record in interaction_id_record_list:
                            interaction_id = interaction_id_record[0]
                            interaction_record = lookup_interaction(interaction_id)
                            compound_id = interaction_record[2]
                            if not compound_id in comp_inter_dict:
                                comp_inter_dict[compound_id] = []
                            param_value = interaction_record[5]
                            comp_inter_dict[compound_id].append(param_value)
                        comp_inter_avg_dict = {}
                        for compound_id in comp_inter_dict.keys():
                            sum = 0.0
                            count = 0
                            for param_value in comp_inter_dict[compound_id]:
                                sum += param_value
                                count += 1
                            avg = sum / float(count)
                            comp_inter_avg_dict[compound_id] = avg
                        compound_sorted_list = []
                        for compound_id in comp_inter_avg_dict.keys():
                            compound_sorted_list.append(compound_id)
                        def cmp(a, b):
                            if comp_inter_avg_dict[a] < comp_inter_avg_dict[b]:
                                return -1
                            elif comp_inter_avg_dict[a] > comp_inter_avg_dict[b]:
                                return 1
                            else:
                                return 0
                        compound_sorted_list.sort(cmp)
                    
                        for compound_id in compound_sorted_list:
                            compound_record = lookup_compound(compound_id)
                            compound_name = compound_record[3]
                            compound_chemblid = compound_record[4]
                            BASE_URL = 'https://www.ebi.ac.uk/chembl/compound/inspect/'
                            if compound_name != '':
                                compound_label = '%s (%s)' % (compound_name, compound_chemblid)
                            else:
                                compound_label = compound_chemblid
                            compound_label = '<a HREF="%s/%s">%s</a>' % (BASE_URL, escape(compound_chemblid), escape(compound_label))
                            #effect_type = ''
                            #param_type = interaction_record[7]
                            param_value = '%.2f' % comp_inter_avg_dict[compound_id]
                            final_results.append([escape(tissue_name), escape(protein_label), escape(expr_level), escape(in_betse), compound_label, escape(param_value)])
                    else:
                        final_results.append([escape(tissue_name), escape(protein_label), escape(expr_level), escape('N'), escape('No interacting compounds'), escape('N/A')])
            result_str = '<table><col width="130"><col width="160"><col width="90"><col width="70"><col width="260"><col width="30">\n'
            #result_str += '<tr><th>Tissue</th><th>Ion channel</th><th>Gene expression</th><th>Interacting compound</th><th>Effect</th><th>Parameter</th><th>Value</th></tr>'
            result_str += '<tr><th>Tissue</th><th>Ion channel</th><th>Gene expression</th><th>In BETSE?</th><th>Interacting compound</th><th>Value</th></tr>'
            for data_record in final_results:
                result_str += '<tr>'
                result_str += '<td align="center">%s</td>\n' % data_record[0]
                result_str += '<td align="center">%s</td>\n' % data_record[1]
                result_str += '<td align="right">%s</td>\n' % data_record[2]
                result_str += '<td align="center">%s</td>\n' % data_record[3]
                result_str += '<td align="center">%s</td>\n' % data_record[4]
                result_str += '<td align="right">%s</td>\n' % data_record[5]
                result_str += '</tr>'
            result_str += '</table>\n'
            result_str += '<br/><br/><a href="%s">Back</a>' % request.get_full_path()
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
    protein_labels = get_list_of_proteins(tissue_list, threshold)
    for protein_label in protein_labels:
        protein_upac = protein_label.split()[0].strip()
        protein_options.append({'upac':protein_upac, 'label':protein_label})
    return HttpResponse(json.dumps(protein_options), content_type="application/json")
