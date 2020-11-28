import pandas as pd
from collections import defaultdict
from assembly_glossary import Assembly_Glossary


class Assembly_Preprocessor:

    def __init__(self):
        self.default_glossary = Assembly_Glossary()

    def tokenize_instructions(self, assembly_functions):
        """
        Convert a list of assembly functions to a list of tokenized expressions.

        Parameters
        ----------
        assembly_functions: List of assembly functions
                Each function in list must have instructions incapsulated in char '.
                For example:
                fun_list = [
                            ['jmp qword ptr [rip + 0x220882]',
                             'jmp qword ptr [rip + 0x220832]'],
                            [...],
                            ...,
                           ]

        Returns
        -------
        token_list: List of all different mnemonics (tokens)\n 
        tokenized_functions: input functions, containing only commands (tokens)
        """
        token_list = []
        tokenized_functions = [[] for _ in range(len(assembly_functions))]
        for function, fun_index in zip(assembly_functions, range(len(assembly_functions))):
            for instruction in function.split("'"):
                command = (instruction.split(" "))[0]
                if command not in ["[","]",","]:
                    tokenized_functions[fun_index].append(command)
                    if command not in token_list:
                        token_list.append(command)                       
        return token_list, tokenized_functions

    def token_categorizer(self, token_list, instruction_glossary=None):
        """
        Assign a category to each token in list, following a specified glossary.

        Parameters
        ----------
        token_list: List of mnemonics (tokens)\n
        instruction_glossary: name of a glossary file (if not specified will be used a default one)
                The selected file should contain assembly mnemonics and relative category. 
                The category will be recognized with a special char, which must be 
                THE FIRST CHAR of the text file, and mnemonics must be in list. 
                For example (special char *):
                *Data transfer instructions*
                mov
                movsd
                movsx
                *Arithmetic instructions*
                ...

        Returns
        -------
        token_dict: Dictionary with keys (category, index) and mnemonics as values
        """
        token_dict = defaultdict(str)
        f_i = e_i = 0
        if instruction_glossary is not None and isinstance(instruction_glossary, str):
            with open(instruction_glossary) as glossary:
                lines = glossary.readlines()
            features = []
            special_char = lines[0][0]
            for element in lines:
                if special_char in element:
                    element = (element.replace(special_char, "")).replace("\n", "")
                    features.append(element)
                    token_dict[(features[f_i], 0)] += ''
                    e_i = 0
                    f_i += 1 
                    continue
                element = (element.replace(" ", "")).replace("\n", "")
                if element in token_list:
                    token_dict[(features[f_i-1], e_i)] += element
                    e_i += 1
            if len(token_list) > (len(lines)-len(features)):
                print("\n\nWARNING: GLOSSARY PROVIDED IS WRONG OR INSUFFICIENT TO CLASSIFY",
                       "INSTRUCTIONS IN THE DATASET!!! \nBE SURE THAT #MNEMONIC IN THE",
                       "GLOSSARY >= THAN #MNEMONIC IN THE DATASET AND THAT the DOCUMENT IS",
                       "IN THE CORRECT FORMAT\n\n")
        else:
            default_dict = self.default_glossary.getDictionary()
            features = self.default_glossary.getCategories()
            token_dict[(features[f_i], 0)] += ''
            for item in default_dict.items():
                if item[0][0] != features[f_i]:
                    token_dict[(features[f_i+1], 0)] += ''
                    f_i += 1
                    e_i = 0
                if item[1] in token_list:
                    token_dict[(features[f_i], e_i)] += item[1]
                    e_i += 1
        return token_dict             

    def assembly_dataframer(self, tokenized_functions, token_dictionary):
        """
        Create a DataFrame having as columns % instructions for each category.

        Parameters
        ----------
        tokenized_functions: list of tokenized assembly functions (only commands)\n
        token_dictionary: Dictionary with keys (category, index) and mnemonics as values
        
        Returns
        -------
        DataFrame: The DataFrame as description
        """
        categories = []
        for item in token_dictionary.items():
            if item[0][0] not in categories:
                categories.append(item[0][0])
        percentage_list = [[] for _ in range(len(tokenized_functions))]
        for function, fun_index in zip(tokenized_functions, range(len(tokenized_functions))):
            i = 0
            duplicate_control = []
            token_occ = [0 for _ in range(len(categories))]
            for item in token_dictionary.items():
                if categories[i] != item[0][0]:
                    i += 1
                if item[1] in function:
                    if item[1] in duplicate_control:
                        continue
                    duplicate_control.append(item[1])
                    for token in function:
                        if token == item[1]:
                            token_occ[i] += 1
            percentage_calc = [0 for _ in range(len(categories))]
            for i in range(len(categories)):
                percentage_calc[i] = round(token_occ[i]/sum(token_occ), 2)
            percentage_list[fun_index] = percentage_calc
        return pd.DataFrame(data=percentage_list, columns=categories)

    def complete_preprocessing(self, assembly_functions, instruction_glossary=None):
        """
        Create a DataFrame using a list of assembly functions, with the specified glossary

        Parameters
        ----------
        assembly_functions: list of functions to preprocess\n
        instruction_glossary: name of a glossary file
                The selected file should contain assembly mnemonics and relative category. 
                The category will be recognized with a special char, which must be 
                THE FIRST CHAR of the text file, and mnemonics must be in list. 
                For example (special char *):
                *Data transfer instructions*
                mov
                movsd
                movsx
                *Arithmetic instructions*
                ...

        Returns
        -------
        DataFrame: The complete DataFrame with instruction percentages
        """
        token_list, tokenized_functions = \
            self.tokenize_instructions(assembly_functions)
        token_dict = self.token_categorizer(token_list, instruction_glossary)
        DataFrame = self.assembly_dataframer(tokenized_functions, token_dict)
        return DataFrame
