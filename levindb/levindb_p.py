import sqlite3

ASSAY_MICROARRAY = 'microarray'
ASSAY_RNASEQ = 'RNA-seq'
ASSAY_IMMUNO = 'immuno'

class LevinDatabase(object):

    def __init__(self, path_db):
        self.path_db = path_db
        self.conn = sqlite3.connect(path_db)
    
    def get_conn(self):
        return self.conn

    def cleanup_conn(self, conn):
        pass

    def cleanup(self):
        self.conn.close()

    def get_all_tissue_names(self):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT Name
            FROM Tissue
            ''')
        resultset = curs.fetchall()
        self.cleanup_conn(conn)
        return resultset

    def get_all_protein_uniprots(self):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT UniProtAccNum
            FROM Protein
            ''')
        resultset = curs.fetchall()
        self.cleanup_conn(conn)
        return resultset

    def get_in_betse_protein(self):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT UniProtAccNum, Name, GeneSymbol
            FROM Protein
            WHERE InBETSE = "Y"
            ''')
        resultset = curs.fetchall()
        self.cleanup_conn(conn)
        return resultset

    def get_in_betse_or_expr_threshold_protein(self, tissue_list, threshold,
            include_betse=True, specificity_option='comprehensive'):
        conn = self.get_conn()
        curs = conn.cursor()
        if include_betse:
            sql = '''
                SELECT UniProtAccNum, Name, GeneSymbol
                FROM Protein
                INNER JOIN Expression
                ON Protein.UniProtAccNum = Expression.ProteinUniProtAccNum
                WHERE (
                    Protein.InBETSE = "Y" OR (
                        Expression.ExprLevel > ? AND Expression.TissueName IN (
                ''' + ','.join(['?'] * len(tissue_list)) + ')))'
        else:
            sql = '''
                SELECT UniProtAccNum, Name, GeneSymbol
                FROM Protein
                INNER JOIN Expression
                ON Protein.UniProtAccNum = Expression.ProteinUniProtAccNum
                WHERE (
                    Expression.ExprLevel > ?
                    AND Expression.TissueName IN (
                ''' + ','.join(['?'] * len(tissue_list)) + '))'
        curs.execute(sql, (threshold,) + tuple(tissue_list))
        resultset = curs.fetchall()
        resultset = list(set(resultset)) # Remove redundant records
        self.cleanup_conn(conn)
        return resultset

    def get_gene_symbol_by_uniprot(self, upac):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT GeneSymbol
            FROM Protein
            WHERE UniProtAccNum=?
            ''', (upac,))
        resultset = curs.fetchone()
        if resultset == None:
            result = ''
        else:
            result = resultset[0]
        self.cleanup_conn(conn)
        return result

    def exists_expr_threshold(self, tissue, upac, threshold, dataset):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT EXISTS(
                SELECT 1
                FROM Expression
                WHERE (
                    TissueName=? AND ProteinUniProtAccNum=?
                    AND DatasetName=? AND ExprLevel>=?
                )
                LIMIT 1
            )
            ''', (tissue, upac, dataset, threshold))
        row = curs.fetchone()
        if row[0] == 1:
            result = True
        else:
            result = False
        self.cleanup_conn(conn)
        return result

    def lookup_protein(self, upac):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT UniProtAccNum, GeneSymbol, Name, ProcessFunction, Ions,
                Gating, InBETSE, IonChannelClassDesc, IonChannelSubClass,
                ChemblId
            FROM Protein
            WHERE UniProtAccNum=?
            ''', (upac,))
        resultset = curs.fetchone()
        if resultset == None:
            result = ['','','','','','','','','','']
        else:
            result = resultset
        self.cleanup_conn(conn)
        return result

    def get_channelpedia_info(self, ion_channel_sub_class):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT ChannelpediaText, ChannelpediaURL
            FROM ChannelSubClass
            WHERE Name=?
            ''', (ion_channel_sub_class,))
        resultset = curs.fetchone()
        if resultset == None:
            result = ['','']
        else:
            result = resultset
        self.cleanup_conn(conn)
        return result

    def get_expr_level_for_dataset(self, upac, tissue, dataset):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT ExprLevel
            FROM Expression
            WHERE ProteinUniProtAccNum=? AND TissueName=? AND DatasetName=?
                AND AssayType=?
            ''', (upac, tissue, dataset, ASSAY_RNASEQ))
        resultset = curs.fetchall()
        self.cleanup_conn(conn)
        return resultset

    def get_expr_level_qual_for_dataset(self, upac, tissue, dataset):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT ExprLevelQual
            FROM Expression
            WHERE ProteinUniProtAccNum=? AND TissueName=? AND DatasetName=?
                AND AssayType=?
            ''', (upac, tissue, dataset, ASSAY_IMMUNO))
        resultset = curs.fetchall()
        self.cleanup_conn(conn)
        return resultset

    def get_interaction_ids_by_uniprot(self, upac, type=None, unit=None):
        conn = self.get_conn()
        curs = conn.cursor()
        if type != None and unit != None:
            curs.execute('''
                SELECT Id
                FROM Interaction
                WHERE TargetUniProtAccNum=? AND AssayType = ?
                    AND StrengthUnits = ?
                ''', (upac, type, unit))
        elif type != None:
            curs.execute('''
                SELECT Id
                FROM Interaction
                WHERE TargetUniProtAccNum=? AND AssayType = ?
                ''', (upac, type))
        elif unit != None:
            curs.execute('''
                SELECT Id
                FROM Interaction
                WHERE TargetUniProtAccNum=? AND StrengthUnits = ?
                ''', (upac, unit))
        else:
            curs.execute('''
                SELECT Id
                FROM Interaction
                WHERE TargetUniProtAccNum=?
                ''', (upac,))
        resultset = curs.fetchall()
        self.cleanup_conn(conn)
        return resultset

    def lookup_interaction(self, id):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT Id, TargetUniProtAccNum, CompoundId, ActionType, ActionDesc,
                Strength, StrengthUnits, AssayType, ChemblId, SourceDBName
            FROM Interaction
            WHERE Id=?
            ''', (id,))
        resultset = curs.fetchone()
        if resultset == None:
            result = ['', '', '', '', '', '', '', '', '', '']
        else:
            result = resultset[0]
        self.cleanup_conn(conn)
        return resultset

    def lookup_compound(self, id):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT Id, SMILES, InChI, Name, ChemblId, Synonyms, ApprovalStatus,
                FirstApprovalYear, SourceDBName
            FROM Compound
            WHERE Id=?
            ''', (id,))
        resultset = curs.fetchone()
        if resultset == None:
            result = ['', '', '', '', '', '', '', '', '']
        else:
            result = resultset
        self.cleanup_conn(conn)
        return result

    def get_specificity(self, tissue_name, upac):
        conn = self.get_conn()
        curs = conn.cursor()
        curs.execute('''
            SELECT SpecificityScore
            FROM Specificity
            WHERE TissueName = ? AND UniProtAccNum = ?
            ''', (tissue_name, upac))
        resultset = curs.fetchone()
        if resultset == None:
            result = ''
        else:
            result = resultset[0]
        self.cleanup_conn(conn)
        return result
