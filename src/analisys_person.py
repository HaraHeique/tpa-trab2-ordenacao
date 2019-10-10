# -*- coding: utf-8 -*-

'''
    performs data analysis for the Person model
'''

import os, sys, csv, datetime, time, math, sort_collection as sort
from models.Person import Person
from typing import List, Dict
from multiprocessing import Process, Queue

__OUTPUT_ANALYZE_FILES_PATH: str = os.path.dirname(os.path.abspath(__file__)) + "/files/analyze"
__EXTENSION_FILES: str = ".csv"
_TIME_OUT: float = 300 # Em segundos
_queue_process: Queue = Queue()

os.makedirs(__OUTPUT_ANALYZE_FILES_PATH, exist_ok=True)

def analyze(directory_path: str, times_of_execution: int) -> bool:
    '''
        parses data from directory files passed as argument. When done, it creates a folder
        named input/analyze, where it contains all the files generated by the analysis.
        returns true if the algorithm can do the correct analysis. Otherwise returns false.
    '''

    hifens: str = "-" * 10
    print("NUMBER OF EXECUTIONS BY ALGORITHM IS: %d\n" %(times_of_execution))
    print("%sSTARTING ANALISYS%s" %(hifens, hifens))
    
    dic_sorting_choices: Dict[str, str] = sort.ALGORITHMS_SORTING_CHOICES
    lst_sorting_choices: List[str] = list(dic_sorting_choices.keys())
    QUICKSORT_KEY = "quicksort"
    filenames: List[str] = __get_all_filenames_from_directory(directory_path, True)

    # Registra os tempos médios de execução dos algoritmos de ordenação
    dic_register_time_execution: Dict[str, Dict[int, float]] = {}

    ## CRIAR ARQUIVOS COM OS REGISTROS E MÉDIA FINAL P/ CADA ALGORITMO COM CADA REGISTRO RODANDO TIME_OF_EXECUTIONS VEZES ##
    for filename in filenames:
        # Coloca os objetos em cache para ser em uma lista de Person
        lst_person: List[Person] = __readCSV_person(os.path.join(directory_path, filename))

        # Variável responsável por matar a execução do processo caso o tempo de execução ultrapasse o dele
        #time_out: float = math.inf

        # Realiza a análise do QuickSort primeiramente, pois ele seta o timeout(20*time_quicksort)
        if (QUICKSORT_KEY in dic_sorting_choices):
            print("{0} records running for {1}...".format(lst_person.__len__(), dic_sorting_choices[QUICKSORT_KEY].upper()))

            dic_time_execution: Dict[str, float] = __register_average_time_execution(lst_person, QUICKSORT_KEY, times_of_execution)

            if QUICKSORT_KEY in dic_register_time_execution:
                dic_register_time_execution[QUICKSORT_KEY][len(lst_person)] = dic_time_execution
            else:
                dic_register_time_execution[QUICKSORT_KEY] = { len(lst_person): dic_time_execution }

            #time_out = 20 * dic_time_execution["average"]

            print("Average time result: {0}ms".format(dic_time_execution["average"]))
            print(hifens*10)

        # Faz a análise para o resto dos algoritmos removendo o quicksort, pois já foi feito
        for algorithm_key in lst_sorting_choices:
            if algorithm_key == QUICKSORT_KEY:
                continue

            print("{0} records running for {1}...".format(lst_person.__len__(), dic_sorting_choices[algorithm_key].upper()))

            dic_time_execution: float = __register_average_time_execution(lst_person, algorithm_key, times_of_execution)

            if algorithm_key in dic_register_time_execution:
                dic_register_time_execution[algorithm_key][len(lst_person)] = dic_time_execution
            else:
                dic_register_time_execution[algorithm_key] = { len(lst_person): dic_time_execution }

            print("Average time result: {0}ms".format(dic_time_execution["average"]))
            print(hifens*10)
    
    ## CRIAR ARQUIVOS COM A MÉDIA DE EXECUÇÃO FINAL E SUA QUANTIDADE DE REGISTROS ##
    __register_average_times_per_num_executions(dic_register_time_execution)

    ## CRIAR UM ARQUIVO FINAL COM TODOS OS ALGORITMOS JUNTOS COM SEUS RESPECTIVOS
    ## TEMPOS MÉDIO DE EXECUÇÃO POR NÚMERO DE REGISTROS
    __register_all_algorithms_average_times_per_num_executions(dic_register_time_execution, dic_sorting_choices)

    print("%sANALISYS FINISHED%s" %(hifens, hifens))

    return True

def __get_all_filenames_from_directory(path: str, orderble: bool = False) -> List[str]:
    lst_filenames: List[str] = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))] 
    if orderble:
        lst_filenames.sort()
        
    return lst_filenames

def __readCSV_person(path_file: str) -> List[Person]:
    try:
        lstPerson: List[Person] = []
        with open(path_file, 'r') as csvfile:
            dataCSV = csv.reader(csvfile, delimiter=',')

            # Ignora a primeira linha do arquivo, pois é o header
            next(dataCSV)

            # Percorre pelas linhas instanciando o objeto da classe Person armazenando dentro da lista
            for dataRow in dataCSV: 
                lstPerson.append(Person(
                    dataRow[2], # id
                    dataRow[0], # email
                    dataRow[1], # gender
                    datetime.datetime.strptime(dataRow[3], "%Y-%m-%d"), # birthdate
                    int(dataRow[4]), # height
                    int(dataRow[5]), # weight
                ))
    except FileNotFoundError as err:
        print(err)
        sys.exit(1)
    except IOError as err:
        print(err)
        sys.exit(1)
    except Exception as err:
        print(err)
        sys.exit(1)
    else:
        return lstPerson

def __writeCSV_analisys_person(dataCSV: List[object], path_file: str) -> None:
    try:
        with open(path_file, 'w') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows(dataCSV)
    except IOError as err:
        print(err)
        sys.exit(1)
    except Exception as err:
        print(err)
        sys.exit(1)

def __calculate_time_of_sort_algorithm(lst_person: List[Person], algorithm_key: str) -> None:
    start_time: float = time.process_time() * 1000
    sort.sort(lst_person, algorithm_key)
    finish_time: float = time.process_time() * 1000

    _queue_process.put(finish_time - start_time)

def __register_average_time_execution(lst_person: List[Person], algorith_key: str, times_of_execution: int) -> Dict[str, float]:
    # Realiza os cálculos de média
    dataCSV_execution_times: List[object] = []
    lst_time_execution: List[float] = []
    
    for execution in range(1, times_of_execution + 1):
        __call_process_timeout(_TIME_OUT, __calculate_time_of_sort_algorithm, [lst_person, algorith_key])
        time_execution: float = _queue_process.get_nowait() if not _queue_process.empty() else _TIME_OUT * 1000
        dataCSV_execution_times.append([execution, time_execution])
        lst_time_execution.append(time_execution)

    average_time: float = sum(lst_time_execution) / times_of_execution

    dic_result: Dict[str, float] = {
        "average": average_time,
        "max": max(lst_time_execution),
        "min": min(lst_time_execution)
    }

    # Cria os dados para serem escritos no arquivo .csv de saída
    header: list = ["Execution", "Average Time(ms)"]
    final_result: list = ["Final Average", average_time]
    dataCSV: list = dataCSV_execution_times
    dataCSV.insert(0, header)
    dataCSV.append(final_result)

    # Seta o nome do arquivo e diretório, onde caso não esteja criado ainda é criado
    filename: str = "{0}_{1}{2}".format(algorith_key, lst_person.__len__(), __EXTENSION_FILES)
    directory: str = os.path.join(__OUTPUT_ANALYZE_FILES_PATH, "average_times_each_record")
    os.makedirs(directory, exist_ok=True)

    # Chama a função genérica que escreve um arquivo
    __writeCSV_analisys_person(dataCSV, os.path.join(directory, filename))

    return dic_result

def __register_average_times_per_num_executions(dic_register_time_execution: Dict[str, Dict[int, object]]) -> None:
    for algorithm_key in dic_register_time_execution.keys():
        dic_algorithm_executions: Dict[int, Dict[str, float]] = dic_register_time_execution[algorithm_key]

        # Pega as chaves que corresponde a número de registros e ordena de forma crescente
        lst_num_records: List[int] = list(dic_algorithm_executions.keys())
        lst_num_records.sort()

        # Setando os dados para o CSV
        header: list = ["Total Records", "Average Time Execution(ms)", "Minimum Value(ms)", "Maximum Value(ms)"]
        dataCSV: list = [header]

        for num_records in lst_num_records:
            dataCSV.append([
                num_records, 
                dic_algorithm_executions[num_records]["average"], 
                dic_algorithm_executions[num_records]["min"],
                dic_algorithm_executions[num_records]["max"]
            ])
        
        # Seta o nome do arquivo e diretório, onde caso não esteja criado ainda é criado
        filename: str = "{0}{1}".format(algorithm_key, __EXTENSION_FILES)
        directory: str = os.path.join(__OUTPUT_ANALYZE_FILES_PATH, "average_times_numbers_records")
        os.makedirs(directory, exist_ok=True)

        # Escreve o arquivo de saída
        __writeCSV_analisys_person(dataCSV, os.path.join(directory, filename))

def __register_all_algorithms_average_times_per_num_executions(dic_register_time_execution: Dict[str, Dict[int, object]], 
                                                               dic_sorting_choices: Dict[str, str]) -> None:
    
    if not dic_register_time_execution:
        return
    
    # Primeira linha contém as informações de número de registro em ordem crescente
    lst_keys_algorithms: List[dict] = list(dic_register_time_execution.keys())
    lst_num_records: List[int] = list(dic_register_time_execution[lst_keys_algorithms[0]].keys())
    lst_num_records.sort()

    dataCSV: list = []

    # Monta os dados para cada algoritmo em cada linha do dataCSV
    for algorithm_key in dic_register_time_execution.keys():
        data_row: List[object] = []

        # Adicionando os valores de média
        for num_records in lst_num_records:
            data_row.append(dic_register_time_execution[algorithm_key][num_records]["average"])

        # Adicionando a qual algoritmo corresponde esses valores de média
        data_row.insert(0, dic_sorting_choices[algorithm_key])
        dataCSV.append(data_row)

    # Monta a header
    header: list = lst_num_records
    header.insert(0, "")
    dataCSV.insert(0, header)

    filename: str = "analisys_all_algorithms_average{0}".format(__EXTENSION_FILES)

    # Escreve o arquivo de saída
    __writeCSV_analisys_person(dataCSV, os.path.join(__OUTPUT_ANALYZE_FILES_PATH, filename))

def __call_process_timeout(timeout: float, target: object, args: list = []) -> None:
    p = Process(target=target, args=args)
    p.start()
    p.join(timeout=timeout)
    p.terminate()

##################################### UNIT LIB TEST #####################################
def execute_test():
    #absolute_path: str = "/media/heik/Arquivos Linux/Documentos/Learning Stuffs/Matérias/TPA/Trabalhos/Trabalho 2/Database"
    #absolute_path: str = "/media/heik/Arquivos Linux/Documentos/Learning Stuffs/Matérias/TPA/Trabalhos/Trabalho 2/Source_Code/src/files/input"
    absolute_path: str =  os.path.dirname(os.path.abspath(__file__)) + "/files/input"
    number_of_executions = 3
    analyze(absolute_path, number_of_executions)

if __name__ == '__main__':
    execute_test()