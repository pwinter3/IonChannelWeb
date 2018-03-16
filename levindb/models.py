# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models


class Channelclass(models.Model):
    name = models.TextField(db_column='Name', primary_key=True)  # Field name made lowercase.
    superclass = models.TextField(db_column='SuperClass')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ChannelClass'


class Channelsubclass(models.Model):
    name = models.TextField(db_column='Name', primary_key=True)  # Field name made lowercase.
    class_field = models.TextField(db_column='Class')  # Field name made lowercase. Field renamed because it was a Python reserved word.

    class Meta:
        managed = False
        db_table = 'ChannelSubClass'


class Channelsuperclass(models.Model):
    name = models.TextField(db_column='Name', primary_key=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ChannelSuperClass'


class Compound(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    smiles = models.TextField(db_column='SMILES')  # Field name made lowercase.
    inchi = models.TextField(db_column='InChI')  # Field name made lowercase.
    name = models.TextField(db_column='Name')  # Field name made lowercase.
    chemblid = models.TextField(db_column='ChemblId')  # Field name made lowercase.
    synonyms = models.TextField(db_column='Synonyms')  # Field name made lowercase.
    approvalstatus = models.TextField(db_column='ApprovalStatus')  # Field name made lowercase.
    firstapprovalyear = models.TextField(db_column='FirstApprovalYear')  # Field name made lowercase.
    sourcedbname = models.TextField(db_column='SourceDBName')  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Compound'


class Dbgene(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    externaldbname = models.TextField(db_column='ExternalDBName')  # Field name made lowercase.
    genbankaccnum = models.TextField(db_column='GenbankAccNum')  # Field name made lowercase.
    probeid = models.TextField(db_column='ProbeID')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DBGene'


class Dbtissue(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    externaldbname = models.TextField(db_column='ExternalDBName')  # Field name made lowercase.
    tissuename = models.TextField(db_column='TissueName')  # Field name made lowercase.
    dbequivalenttissuename = models.TextField(db_column='DBEquivalentTissueName')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DBTissue'


class Expression(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    tissuename = models.TextField(db_column='TissueName')  # Field name made lowercase.
    proteinuniprotaccnum = models.TextField(db_column='ProteinUniProtAccNum')  # Field name made lowercase.
    exprlevel = models.FloatField(db_column='ExprLevel')  # Field name made lowercase.
    exprunits = models.TextField(db_column='ExprUnits')  # Field name made lowercase.
    assaytype = models.TextField(db_column='AssayType')  # Field name made lowercase.
    datasetname = models.TextField(db_column='DatasetName')  # Field name made lowercase.
    sourcedbname = models.TextField(db_column='SourceDBName')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Expression'


class Externaldb(models.Model):
    name = models.TextField(db_column='Name', primary_key=True)  # Field name made lowercase.
    url = models.TextField(db_column='URL')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ExternalDB'


class Genbankuniprot(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    genbankaccnum = models.TextField(db_column='GenbankAccNum')  # Field name made lowercase.
    uniprotaccnum = models.TextField(db_column='UniProtAccNum')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GenbankUniprot'


class Interaction(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    targetuniprotaccnum = models.TextField(db_column='TargetUniProtAccNum')  # Field name made lowercase.
    compoundid = models.IntegerField(db_column='CompoundId')  # Field name made lowercase.
    actiontype = models.TextField(db_column='ActionType')  # Field name made lowercase.
    actiondesc = models.TextField(db_column='ActionDesc')  # Field name made lowercase.
    strength = models.FloatField(db_column='Strength')  # Field name made lowercase.
    strengthunits = models.TextField(db_column='StrengthUnits')  # Field name made lowercase.
    assaytype = models.TextField(db_column='AssayType')  # Field name made lowercase.
    chemblid = models.TextField(db_column='ChemblId')  # Field name made lowercase.
    sourcedbname = models.TextField(db_column='SourceDBName')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Interaction'


class Pdb(models.Model):
    id = models.IntegerField(db_column='Id', primary_key=True)  # Field name made lowercase.
    uniprotaccnum = models.TextField(db_column='UniProtAccNum')  # Field name made lowercase.
    pdbid = models.TextField(db_column='PDBID')  # Field name made lowercase.
    humanonly = models.TextField(db_column='HumanOnly')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'PDB'


class Protein(models.Model):
    uniprotaccnum = models.TextField(db_column='UniProtAccNum', primary_key=True)  # Field name made lowercase.
    genesymbol = models.TextField(db_column='GeneSymbol')  # Field name made lowercase.
    name = models.TextField(db_column='Name')  # Field name made lowercase.
    processfunction = models.TextField(db_column='ProcessFunction')  # Field name made lowercase.
    ions = models.TextField(db_column='Ions')  # Field name made lowercase.
    gating = models.TextField(db_column='Gating')  # Field name made lowercase.
    inbetse = models.TextField(db_column='InBETSE')  # Field name made lowercase.
    ionchannelclassdesc = models.TextField(db_column='IonChannelClassDesc')  # Field name made lowercase.
    ionchannelsubclass = models.TextField(db_column='IonChannelSubClass')  # Field name made lowercase.
    chemblid = models.TextField(db_column='ChemblId')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Protein'


class Tissue(models.Model):
    name = models.TextField(db_column='Name', primary_key=True)  # Field name made lowercase.
    btoid = models.TextField(db_column='BTOId', unique=True)  # Field name made lowercase.
    parenttissuename = models.TextField(db_column='ParentTissueName')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tissue'
