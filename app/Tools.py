import logging
import os
import time

from PySide2 import QtWidgets

import AlignDelegate
import DatabaseGestionSqlite
import MyTableModel
import constantes


# Les fonctions dans Tools ont besoin de l'UI. Donc je passe une instance de l'UI.

class Tools(QtWidgets.QWidget):
    def __init__(self, window_instance):
        self.window_instance = window_instance
        super(Tools, self).__init__()
        self.list_result_saut = []

    def is_db_empty(self):
        with DatabaseGestionSqlite.DatabaseGestionSqlite() as db_connection:  # with allows you to use a context manager that will automatically call the disconnect function when you exit the scope
            if db_connection.error_db_connection is None:
                self.window_instance.textEdit.setText("Base de donnée vide ? Vérification en cours...")
                db_connection.sql_query_execute(f'SELECT * FROM serveur_vmware')
                rows_vmware = db_connection.cursor.fetchall()
                if not rows_vmware:
                    self.window_instance.textEdit.setText("Base VMware vide.")
                    return True
                db_connection.sql_query_execute(f'SELECT * FROM serveur_opca')
                rows_opca = db_connection.cursor.fetchall()
                if not rows_opca:
                    self.window_instance.textEdit.setText("Base OPCA vide.")
                    return True
                return False

    def search(self, search_list):
        results_query_search = []
        nbr_result_ko = 0
        nbr_result_ok = 0
        # red_text = "<span style=\" color:#ff0000;\" >"
        # text_end = "</span>"
        # green_text = "<span style=\" color:#5ea149;\" >"
        search_choice = self.window_instance.comboBox.currentText()
        self.window_instance.textEdit.setText("Connexion à la base de données...")
        QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
        # dict_search_choice = {'Serveur': 'serveur_name', 'Host': 'host_name', 'Application': 'appli_name'}
        # search_choice = dict_search_choice.get(search_choice, 'default')  # We get the field to use for the select and where in the SQL query and if it is neither of them we put "default"
        logging.debug(f"search_choice: {search_choice}")
        logging.debug(f"search_list: {search_list}")

        with DatabaseGestionSqlite.DatabaseGestionSqlite() as db_connection:  # with allows you to use a context manager that will automatically call the disconnect function when you exit the scope
            if db_connection.error_db_connection is None:
                if search_choice == 'Equipement':
                    if self.is_db_empty():
                        pass
                    else:
                        # If search is empty, search and display all results
                        self.window_instance.textEdit.setText("Recherche en cours...")
                        QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
                        if not search_list:
                            db_connection.sql_query_execute(f"""
                                    select DISTINCT t.serveur_name,
                                           coalesce(v.management_name, o.management_name, 'N/A') management_name,
                                           coalesce(v.dns_name, o.dns_name, 'N/A') dns_name,
                                           coalesce(c.environment_name, ca.environment_name, 'N/A') environment_name,
                                           coalesce(c.device_type, ca.device_type, 'N/A') device_type,
                                           coalesce(c.operational_status, ca.operational_status, 'N/A') operational_status,
                                           coalesce(c.system_type, ca.system_type, 'N/A') system_type,
                                           coalesce(c.asset, 'N/A') asset
                                    from (
                                      select upper(serveur_name) serveur_name from serveur_cmdb_all union
                                      select upper(serveur_name) serveur_name from serveur_cmdb union
                                      select upper(serveur_name) from serveur_vmware union
                                      select upper(serveur_name) from serveur_opca
                                    ) t
                                    left join serveur_cmdb_all ca on ca.serveur_name = t.serveur_name COLLATE NOCASE
                                    left join serveur_cmdb c on c.serveur_name = t.serveur_name COLLATE NOCASE
                                    left join serveur_vmware v on v.serveur_name = t.serveur_name COLLATE NOCASE
                                    left join serveur_opca o on o.serveur_name = t.serveur_name COLLATE NOCASE
                                """)
                            results_query_search = db_connection.cursor.fetchall()
                        else:  # if search is not empty
                            search_list_len = len(search_list)
                            step_search = 0
                            self.window_instance.textEdit.setText("Recherche en cours...")
                            QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
                            # For each search string in list
                            for file_number_search, search_string in enumerate(search_list, 1):
                                search_string = str.strip(search_string)  # delete spaces before and after the
                                self.window_instance.textEdit.setText(f"Recherche en cours de {search_string}...")
                                db_connection.sql_query_execute(f"""
                                select DISTINCT t.serveur_name,
                                           coalesce(v.management_name, o.management_name, 'N/A') management_name,
                                           coalesce(v.dns_name, o.dns_name, 'N/A') dns_name,
                                           coalesce(c.environment_name, ca.environment_name, 'N/A') environment_name,
                                           coalesce(c.device_type, ca.device_type, 'N/A') device_type,
                                           coalesce(c.operational_status, ca.operational_status, 'N/A') operational_status,
                                           coalesce(c.system_type, ca.system_type, 'N/A') system_type,
                                           coalesce(c.asset, 'N/A') asset
                                    from (
                                      select upper(serveur_name) serveur_name from serveur_cmdb_all union
                                      select upper(serveur_name) serveur_name from serveur_cmdb union
                                      select upper(serveur_name) from serveur_vmware union
                                      select upper(serveur_name) from serveur_opca
                                    ) t
                                    left join serveur_cmdb_all ca on ca.serveur_name = t.serveur_name COLLATE NOCASE
                                    left join serveur_cmdb c on c.serveur_name = t.serveur_name COLLATE NOCASE
                                    left join serveur_vmware v on v.serveur_name = t.serveur_name COLLATE NOCASE
                                    left join serveur_opca o on o.serveur_name = t.serveur_name COLLATE NOCASE
                                WHERE v.dns_name LIKE \'%{search_string}%\' 
                                    OR v.serveur_name LIKE \'%{search_string}%\'
                                    OR o.dns_name LIKE \'%{search_string}%\' 
                                    OR o.serveur_name LIKE \'%{search_string}%\'
                                    OR c.serveur_name LIKE \'%{search_string}%\'
                                    OR ca.serveur_name LIKE \'%{search_string}%\'
                                """)
                                rows_result_sql = db_connection.cursor.fetchall()
                                if not rows_result_sql:
                                    nbr_result_ko += 1
                                    results_query_search.append((search_string, 'Non présent dans les exports', 'Non présent dans les exports', 'Non présent dans les exports', 'Non présent dans les exports', 'Non présent dans les exports', 'Non présent dans les exports', 'Non présent dans les exports'))
                                if rows_result_sql:
                                    nbr_item_in_list = len(rows_result_sql)
                                    results_query_search.extend(rows_result_sql)
                                    nbr_result_ok = nbr_result_ok + nbr_item_in_list
                                if search_list_len > 1:  # To avoid having the progress bar when doing a search on only one item to not waste time
                                    # Update of the progress bar
                                    self.window_instance.progressBar.show()
                                    pourcentage_number_1 = (file_number_search * 100 - 1) // search_list_len
                                    for between_pourcentage_1 in range(step_search, pourcentage_number_1):
                                        time.sleep(0.005)
                                        pourcentage_text_1 = f"Processing of {between_pourcentage_1}% ..."
                                        self.window_instance.statusBar.showMessage(pourcentage_text_1)
                                        self.window_instance.progressBar.setValue(between_pourcentage_1)
                                        step_search = (file_number_search * 100 - 1) // search_list_len
                        nbr = 0  # To get number of results
                        list_result = []
                        # list_result_saut = []

                    for nbr, result_query_search in enumerate(results_query_search, 1):
                        #  print(result_query_search)
                        serveur_name, management_name, dns_name, environment_name, device_type, operational_status, system_type, asset = result_query_search  # unpacking
                        # if management_name == 'Non présent dans les exports':
                        #     list_result.append(f"{serveur_name} --> {red_text}{management_name}{text_end} --> {dns_name} --> {environment_name} --> {device_type} --> {operational_status} --> {system_type} --> {asset}")
                        # else:
                        #     list_result.append(f"{serveur_name} --> {green_text}{management_name}{text_end} --> {dns_name} --> {environment_name} --> {device_type} --> {operational_status} --> {system_type} --> {asset}")

                        list_result.append(f"{serveur_name};{management_name};{dns_name};{environment_name};{device_type};{operational_status};{system_type};{asset}")
                        self.list_result_saut = "\n".join(list_result)
                    # print(self.list_result_saut)
                    # Display result in text edit
                    # self.window_instance.textEdit.setText(list_result_saut)
                    self.window_instance.textEdit.setText("CTRL+A pour sélectionner toutes les données.\nCTRL+C pour copier les données des cellules sélectionnées.\nCTRL+V pour coller dans un fichier texte au format .CSV\nCliquer sur les noms des colonnes pour trier")
                    # Display data results in tableview
                    # header table view
                    header = ['Nom', 'vCenter ou ESXi (vmware), Management Node (opca)', 'Nom DNS (vmware)', 'Environnement/Application (CMDB)', 'Type (CMDB)', 'Status opérationnel (CMDB)', 'Type de Système (CMDB)', 'Asset (CMDB)']
                    # Create instance table view
                    table_model = MyTableModel.MyTableModel(results_query_search, header, window_instance=self.window_instance)
                    self.window_instance.tableView.setModel(table_model)
                    # install event filter pour pouvoir récupérer un évenement d'appui de CTRL+C (copy) quand on a sélectionné des cellules
                    self.window_instance.tableView.installEventFilter(table_model)
                    # set color and style header
                    # stylesheet = "::section{Background-color:rgb(179, 224, 229);border-radius:14px;}"   # Pour ne pas avoir les bordures des cases du header
                    stylesheet = "::section{Background-color:rgb(179, 224, 229)}"  # Couleur bleu ciel pour l'entête du tableau
                    self.window_instance.tableView.horizontalHeader().setStyleSheet(stylesheet)
                    # set font
                    # font = QtGui.QFont("Courier New", 14)
                    # self.tableView.setFont(font)
                    # main_window.tableView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)  # Ajuster la zone tableview aux colonnes (ne fonctionne pas ??!)
                    # set column width to fit contents (set font first!)
                    self.window_instance.tableView.resizeColumnsToContents()
                    # stretch the last column to the view so that the table view fit the layout
                    self.window_instance.tableView.horizontalHeader().setStretchLastSection(True)
                    delegate = AlignDelegate.AlignDelegate(self.window_instance.tableView)
                    # main_window.tableView.setItemDelegateForColumn(2, delegate)  # Pour Centrer le texte de la colonne id 2 (donc la troisième)
                    self.window_instance.tableView.setItemDelegate(delegate)  # for all columns
                    # enable sorting
                    self.window_instance.tableView.setSortingEnabled(True)
                    self.window_instance.statusBar.showMessage(f"Résultats : {str(nbr)} | OK : {str(nbr_result_ok)} | KO : {str(nbr_result_ko)}")
                    self.window_instance.progressBar.reset()
                    # self.window_instance.progressBar.hide()
                elif search_choice == 'Host (ESXi ou CN)':
                    if self.is_db_empty():
                        pass
                    else:
                        # If search is empty, search and display all results
                        self.window_instance.textEdit.setText("Recherche en cours...")
                        QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
                        if not search_list:
                            db_connection.sql_query_execute(f'''
                                SELECT 
                                host_name, 
                                management_name 
                                FROM serveur_vmware
                            ''')
                            rows_vmware = db_connection.cursor.fetchall()
                            db_connection.sql_query_execute(f'''
                                SELECT 
                                host_name, 
                                management_name 
                                FROM serveur_opca
                            ''')
                            rows_opca = db_connection.cursor.fetchall()
                            results_query_search.extend(rows_vmware)
                            results_query_search.extend(rows_opca)
                        else:  # if search is not empty
                            search_list_len = len(search_list)
                            step_search = 0
                            self.window_instance.textEdit.setText("Recherche en cours...")
                            QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
                            # For each search string in list
                            for file_number_search, search_string in enumerate(search_list, 1):
                                search_string = str.strip(search_string)  # delete spaces before and after the
                                self.window_instance.textEdit.setText(f"Recherche en cours de {search_string}...")
                                db_connection.sql_query_execute(f'''
                                    SELECT 
                                    host_name, 
                                    management_name 
                                    FROM serveur_vmware 
                                    WHERE host_name LIKE \'%{search_string}%\'
                                ''')
                                rows_vmware = db_connection.cursor.fetchall()
                                db_connection.sql_query_execute(f'''
                                    SELECT 
                                    host_name, 
                                    management_name 
                                    FROM serveur_opca 
                                    WHERE host_name 
                                    LIKE \'%{search_string}%\'
                                ''')
                                rows_opca = db_connection.cursor.fetchall()
                                if not rows_opca and not rows_vmware:
                                    results_query_search.append((search_string, 'Non présent dans les exports'))
                                if rows_vmware:
                                    results_query_search.extend(rows_vmware)
                                if rows_opca:
                                    results_query_search.extend(rows_opca)
                                if search_list_len > 1:  # To avoid having the progress bar when doing a search on only one item to not waste time
                                    # Update of the progress bar
                                    self.window_instance.progressBar.show()
                                    pourcentage_number_1 = (file_number_search * 100 - 1) // search_list_len
                                    for between_pourcentage_1 in range(step_search, pourcentage_number_1):
                                        time.sleep(0.005)
                                        pourcentage_text_1 = f"Processing of {between_pourcentage_1}% ..."
                                        self.window_instance.statusBar.showMessage(pourcentage_text_1)
                                        self.window_instance.progressBar.setValue(between_pourcentage_1)
                                        step_search = (file_number_search * 100 - 1) // search_list_len
                        results_query_search = list(dict.fromkeys(results_query_search))  # Remove the duplicates
                        results_query_search = [x for x in results_query_search if "0" not in x]  # Remove the results that is "0" (for opca data)
                        nbr = 0  # To get number of results
                        list_result = []
                        # list_result_saut = []
                        for nbr, result_query_search in enumerate(results_query_search, 1):
                            serveur_name, management_name = result_query_search  # unpacking
                            # if management_name == 'Non présent dans les exports':
                            #     list_result.append(f"{serveur_name} --> {red_text}{management_name}{text_end}")
                            # else:
                            #     list_result.append(f"{serveur_name} --> {green_text}{management_name}{text_end}")
                            list_result.append(f"{serveur_name};{management_name}")
                            self.list_result_saut = "\n".join(list_result)
                            # print(self.list_result_saut)
                            # Display result in text edit
                            # self.window_instance.textEdit.setText(list_result_saut)
                            self.window_instance.textEdit.setText("CTRL+C pour copier les données des cellules sélectionnées.\nCTRL+A pour sélectionner toutes les données.\nMenu \"Fichier > Exporter le résultat\" pour exporter le résultat en CSV\nCliquer sur les noms des colonnes pour trier")
                            # Display data results in tableview
                        # header table view
                        header = ['Nom de l\'ESXi (vmware) ou du Management Node (opca)', 'vCenter (vmware) ou Management Node (opca)']
                        # Create instance table view
                        table_model = MyTableModel.MyTableModel(results_query_search, header, window_instance=self.window_instance)
                        self.window_instance.tableView.setModel(table_model)
                        # install event filter pour pouvoir récupérer un évenement d'appui de CTRL+C (copy) quand on a sélectionné des cellules
                        self.window_instance.tableView.installEventFilter(table_model)
                        # set color and style header
                        # stylesheet = "::section{Background-color:rgb(179, 224, 229);border-radius:14px;}"   # Pour ne pas avoir les bordures des cases du header
                        stylesheet = "::section{Background-color:rgb(179, 224, 229)}"  # Couleur bleu ciel pour l'entête du tableau
                        self.window_instance.tableView.horizontalHeader().setStyleSheet(stylesheet)
                        # set font
                        # font = QtGui.QFont("Courier New", 14)
                        # self.tableView.setFont(font)
                        # main_window.tableView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)  # Ajuster la zone tableview aux colonnes (ne fonctionne pas ??!)
                        # set column width to fit contents (set font first!)
                        self.window_instance.tableView.resizeColumnsToContents()
                        # stretch the last column to the view so that the table view fit the layout
                        self.window_instance.tableView.horizontalHeader().setStretchLastSection(True)
                        delegate = AlignDelegate.AlignDelegate(self.window_instance.tableView)
                        # main_window.tableView.setItemDelegateForColumn(2, delegate)  # Pour Centrer le texte de la colonne id 2 (donc la troisième)
                        self.window_instance.tableView.setItemDelegate(delegate)  # for all columns
                        # enable sorting
                        self.window_instance.tableView.setSortingEnabled(True)
                        # main_window.statusBar.showMessage(f"Results : {str(nbr)} | OK : {str(nbr_result_ok)} | KO : {str(nbr_result_ko)}")
                        self.window_instance.statusBar.showMessage(f"Résultats : {str(nbr)}")
                        self.window_instance.progressBar.reset()
                        # self.window_instance.progressBar.hide()
                elif search_choice == 'Application':
                    if self.is_db_empty():
                        pass
                    else:
                        # If search is empty, search and display all results
                        self.window_instance.textEdit.setText("Recherche en cours...")
                        QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
                        if not search_list:
                            db_connection.sql_query_execute(f"""
                                select DISTINCT ifnull(c.environment_name, 'N/A'),
                                       t.serveur_name
                                from (
                                  select serveur_name from serveur_cmdb union
                                  select serveur_name from serveur_vmware union
                                  select serveur_name from serveur_opca
                                ) t
                                left join serveur_cmdb c on c.serveur_name = t.serveur_name
                                left join serveur_vmware v on v.serveur_name = t.serveur_name
                                left join serveur_opca o on o.serveur_name = t.serveur_name
                            """)
                            results_query_search = db_connection.cursor.fetchall()
                        else:  # if search is not empty
                            search_list_len = len(search_list)
                            step_search = 0
                            self.window_instance.textEdit.setText("Recherche en cours...")
                            QtWidgets.QApplication.processEvents()  # Force a refresh of the UI
                            # For each search string in list
                            for file_number_search, search_string in enumerate(search_list, 1):
                                search_string = str.strip(search_string)  # delete spaces before and after the
                                self.window_instance.textEdit.setText(f"Recherche en cours de {search_string}...")
                                db_connection.sql_query_execute(f"""
                                    select DISTINCT c.environment_name,
                                           t.serveur_name
                                    from (
                                      select serveur_name from serveur_cmdb union
                                      select serveur_name from serveur_vmware union
                                      select serveur_name from serveur_opca
                                    ) t
                                    left join serveur_cmdb c on c.serveur_name = t.serveur_name
                                    left join serveur_vmware v on v.serveur_name = t.serveur_name
                                    left join serveur_opca o on o.serveur_name = t.serveur_name 
                                    WHERE c.environment_name LIKE \'%{search_string}%\'
                                """)
                                rows_result_sql = db_connection.cursor.fetchall()
                                if not rows_result_sql:
                                    nbr_result_ko += 1
                                    results_query_search.append((search_string, 'Non présent dans les exports'))
                                if rows_result_sql:
                                    nbr_item_in_list = len(rows_result_sql)
                                    results_query_search.extend(rows_result_sql)
                                    nbr_result_ok = nbr_result_ok + nbr_item_in_list
                                if search_list_len > 1:  # To avoid having the progress bar when doing a search on only one item to not waste time
                                    # Update of the progress bar
                                    self.window_instance.progressBar.show()
                                    pourcentage_number_1 = (file_number_search * 100 - 1) // search_list_len
                                    for between_pourcentage_1 in range(step_search, pourcentage_number_1):
                                        time.sleep(0.005)
                                        pourcentage_text_1 = f"Action en cours de {between_pourcentage_1}% ..."
                                        self.window_instance.statusBar.showMessage(pourcentage_text_1)
                                        self.window_instance.progressBar.setValue(between_pourcentage_1)
                                        step_search = (file_number_search * 100 - 1) // search_list_len
                        nbr = 0  # To get number of results
                        list_result = []
                        # list_result_saut = []
                        for nbr, result_query_search in enumerate(results_query_search, 1):
                            # print(result_query_search)
                            environment_name, serveur_name = result_query_search  # unpacking
                            # if serveur_name == 'Non présent dans les exports':
                            #     list_result.append(f"{environment_name} --> {red_text}{serveur_name}{text_end}")
                            # else:
                            #     list_result.append(f"{environment_name} --> {green_text}{serveur_name}{text_end}")
                            list_result.append(f"{environment_name};{serveur_name}")
                            self.list_result_saut = "\n".join(list_result)
                            # print(self.list_result_saut)
                            # Display result in text edit
                            # self.window_instance.textEdit.setText(list_result_saut)
                            self.window_instance.textEdit.setText("CTRL+C pour copier les données des cellules sélectionnées.\nCTRL+A pour sélectionner toutes les données.\nMenu \"Fichier > Exporter le résultat\" pour exporter le résultat en CSV\nCliquer sur les noms des colonnes pour trier")
                            # Display data results in tableview
                        # header table view
                        header = ['Application (CMDB)', 'Nom']
                        # Create instance table view
                        table_model = MyTableModel.MyTableModel(results_query_search, header, window_instance=self.window_instance)
                        self.window_instance.tableView.setModel(table_model)
                        # install event filter pour pouvoir récupérer un évenement d'appui de CTRL+C (copy) quand on a sélectionné des cellules
                        self.window_instance.tableView.installEventFilter(table_model)
                        # set color and style header
                        # stylesheet = "::section{Background-color:rgb(179, 224, 229);border-radius:14px;}"   # Pour ne pas avoir les bordures des cases du header
                        stylesheet = "::section{Background-color:rgb(179, 224, 229)}"  # Couleur bleu ciel pour l'entête du tableau
                        self.window_instance.tableView.horizontalHeader().setStyleSheet(stylesheet)
                        # set font
                        # font = QtGui.QFont("Courier New", 14)
                        # self.tableView.setFont(font)
                        # main_window.tableView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)  # Ajuster la zone tableview aux colonnes (ne fonctionne pas ??!)
                        # set column width to fit contents (set font first!)
                        self.window_instance.tableView.resizeColumnsToContents()
                        # stretch the last column to the view so that the table view fit the layout
                        self.window_instance.tableView.horizontalHeader().setStretchLastSection(True)
                        delegate = AlignDelegate.AlignDelegate(self.window_instance.tableView)
                        # main_window.tableView.setItemDelegateForColumn(2, delegate)  # Pour Centrer le texte de la colonne id 2 (donc la troisième)
                        self.window_instance.tableView.setItemDelegate(delegate)  # for all columns
                        # enable sorting
                        self.window_instance.tableView.setSortingEnabled(True)
                        self.window_instance.statusBar.showMessage(f"Résultats : {str(nbr)} | OK : {str(nbr_result_ok)} | KO : {str(nbr_result_ko)}")
                        self.window_instance.progressBar.reset()
                        # self.window_instance.progressBar.hide()
            else:
                self.window_instance.textEdit.setText(db_connection.message_error_connection_db)

    def is_file_authorized(self, file):
        """ If the file is in the list of authorized_files, we copy the file
        :param file: Name of the file with its extension
        :return: A booleen True if the file is part of the authorized list or False if not
        """

        # Remplacement du bloc ci-dessous par l'opérateur conditionnel ternaire après
        # if file in self.window_instance.authorized_files_source_list:  # Lire l'attribut de l'instance qui a déjà été initialisé
        #     logging.debug(f"is_file_authorized : \"{file}\" is an authorized file.")
        #     file_authorized = True
        # else:
        #     logging.debug(f"is_file_authorized : \"{file}\" is not an authorized file.")
        #     file_authorized = False

        # Opérateur conditionnel ternaire pour remplacer le bloc ci-dessus
        file_authorized = True if file in self.window_instance.authorized_files_source_list else False
        logging.debug(f"is_file_authorized : Is file \"{file}\" is an authorized file = {file_authorized}")

        return file_authorized

    def list_exports(self, export_type):
        # Check if there are any exports in the folder concerned
        if not os.listdir(fr"{constantes.EXPORTS_DIR}\exports_{export_type}"):
            self.window_instance.textEdit.setText(f"Le répertoire des exports exports_{export_type} est vide.")
        else:
            # Creates a list of files that are in the export folder where each element is of the type 'C:\\path\file.ext'
            files_paths_list = []
            exports_files_folder_path = fr"{constantes.EXPORTS_DIR}\exports_{export_type}"  # Retrieving the path of the export folder
            for root, dirs, files in os.walk(exports_files_folder_path):
                for file in files:
                    files_paths_list.append(os.path.join(root, file))
            number_authorized = number_not_authorized = 0
            files_authorized_list = []
            files_not_authorized_list = []
            for file_path in files_paths_list:
                file = os.path.basename(file_path)
                file_is_authorized = self.is_file_authorized(file)
                if file_is_authorized:
                    number_authorized += 1
                    files_authorized_list.append(file)
                else:
                    number_not_authorized += 1
                    files_not_authorized_list.append(file)

            if files_authorized_list:
                list_result_cr_authorized = "\n".join(files_authorized_list)
                result_search_authorized = f"Nombre de fichiers autorisés trouvés dans le répertoire des exports export_{export_type} : {str(number_authorized)}\n\n{list_result_cr_authorized}"
            else:
                result_search_authorized = "Pas de fichiers autorisés trouvés dans le répertoire des exports."

            if files_not_authorized_list:
                list_result_cr_not_authorized = "\n".join(files_not_authorized_list)
                result_search_not_authorized = f"Nombre de fichiers non-autorisés trouvés dans le répertoire des exports export_{export_type} : {str(number_not_authorized)}\n\n{list_result_cr_not_authorized}"
            else:
                result_search_not_authorized = f"Pas de fichiers non-autorisés trouvés dans le répertoire des exports export_{export_type}."

            self.window_instance.textEdit.setText(f"{result_search_authorized}\n\n{result_search_not_authorized}")
