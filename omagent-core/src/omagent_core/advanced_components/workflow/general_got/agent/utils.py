from typing import Dict, List, Set
import json_repair
import logging
import json

def sort_num_errors(node_dict: Dict) -> float:
    """
    Function to locally count the number of errors that serves as a score.

    Args:
        node_dict (Dict): Dictionary containing the original and current task input lists.
            Expected keys:
            - original_task_input: The input list to be sorted
            - current_task_input: The current solution list

    Returns:
        float: Number of errors in the current solution. Returns 300 if parsing fails.
    """

    try:
        unsorted_list = node_dict["original_task_input"]
        if (
            "original_task_input" in node_dict
            and node_dict["original_task_input"] != ""
            and node_dict["original_task_input"] is not None
            and len(node_dict["original_task_input"]) < len(unsorted_list) - 5
        ):
            unsorted_list = node_dict["original_task_input"]
        correct_list = sorted(json_repair.loads(str(node_dict["original_task_input"])))
        current_list = json_repair.loads(str(node_dict["current_task_input"]))
        num_errors = 0
        for i in range(10):
            num_errors += abs(
                sum([1 for num in current_list if num == i])
                - sum([1 for num in correct_list if num == i])
            )
        num_errors += sum(
            [1 for num1, num2 in zip(current_list, current_list[1:]) if num1 > num2]
        )
        return num_errors
    except:
        return 300
    
def keyword_count_num_errors(all_possible_countries: List[str], node_dict: Dict) -> float:
    """
    Function to locally count the number of errors that serves as a score.

    Args:
        all_possible_countries (List[str]): List of keywords (countries) to count.
        node_dict (Dict): Dictionary containing the original text and current counting results.
            Expected keys:
            - original_task_input: The input text to analyze
            - current_task_input: The current frequency dictionary of keywords

    Returns:
        float: Number of counting errors. Returns 100 if parsing fails.

    Raises:
        ValueError: If original_task_input is missing or empty.
    """

    try:
        
        if (
            "original_task_input" in node_dict
            and (node_dict["original_task_input"] != "" or node_dict["current_task_input"] == "{}")
        ):
            text = node_dict["original_task_input"]
            correct_freq_dict = dict()
            for country in all_possible_countries:
                # find number of times country appears in text
                num_occurrences = text.count(country)
                correct_freq_dict[country] = num_occurrences
        else:
            raise ValueError("Please provide ground truth")
        try:
            current_freq_dict = json.loads(node_dict["current_task_input"])
        except:
            current_freq_dict = node_dict["current_task_input"]
        countries_not_in_current = set(correct_freq_dict.keys()) - set(
            current_freq_dict.keys()
        )
        countries_not_in_correct = set(current_freq_dict.keys()) - set(
            correct_freq_dict.keys()
        )
        # count the number of errors
        num_errors = 0
        for country in countries_not_in_current:
            num_errors += abs(correct_freq_dict[country])
        for country in countries_not_in_correct:
            num_errors += abs(current_freq_dict[country])
        for country in set(correct_freq_dict.keys()) & set(current_freq_dict.keys()):
            num_errors += abs(correct_freq_dict[country] - current_freq_dict[country])
        return num_errors
    except:
        return 100
    
def string_to_set(string: str) -> Set[int]:
    """Convert a string representation of a list into a set of integers.

    Args:
        string (str): String representation of a list (e.g., "[1,2,3]").

    Returns:
        Set[int]: Set containing the integer elements.

    Raises:
        AssertionError: If the input string is not in proper list format.
    """
    assert string[0] == "[" and string[-1] == "]", "String is not a list. {}".format(string)
    return {int(num) for num in string[1:-1].split(",")}

def set_intersection_num_errors(set1, node_dict: Dict) -> float:
    """
    Function to locally count the number of errors that serves as a score.

    Args:
        set1: First set for intersection operation.
        node_dict (Dict): Dictionary containing the second set and current solution.
            Expected keys:
            - pre_task_input: The second set for intersection
            - current_task_input: The current intersection result

    Returns:
        float: Number of errors in the intersection result.
    """

    # try:
    set1 = string_to_set(str(set1))
    try:
        set2 = string_to_set(str(node_dict["pre_task_input"]))
    except:
        set2 = [v for k, v in node_dict["pre_task_input"].items()]
        set2 = set([item for sublist in set2 for item in sublist])

    common = sorted(list(set1 & set2))
    llm_solution = sorted(list(string_to_set(str(node_dict["current_task_input"]))))
    num_errors = 0
    common_idx = 0
    llm_idx = 0
    while common_idx < len(common) and llm_idx < len(llm_solution):
        if common[common_idx] == llm_solution[llm_idx]:
            common_idx += 1
            llm_idx += 1
        elif common[common_idx] < llm_solution[llm_idx]:
            common_idx += 1
            num_errors += 1
        elif common[common_idx] > llm_solution[llm_idx]:
            llm_idx += 1
            num_errors += 1
    num_errors += len(common) - common_idx + len(llm_solution) - llm_idx
    return num_errors
    # except:
    #     return 1000
    


def sort_parse_refine_answer(text: str) -> List[Dict]:
    """Parse and extract the sorted list from the language model's response.

    Args:
        text (str): Raw response text from the language model.

    Returns:
        List[Dict]: Parsed answer containing the sorted list.
            Returns empty list if parsing fails.

    Notes:
        - Extracts lists enclosed in square brackets
        - Uses the last valid answer if multiple answers are found
        - Ignores lines containing "Input" or "Incorrectly"
    """

    answers = text.strip().split("\n")
    answers = [
        answer for answer in answers if "[" in answer and "]" in answer
    ]
    if any(["Output" in answer for answer in answers]):
        # cut elements until last output is found
        for answer in reversed(answers):
            if "Output" in answer:
                answers = answers[answers.index(answer) :]
                break

    answers = [
        answer[answer.index("[") : answer.index("]") + 1]
        for answer in answers if "Input" not in answer and "Incorrectly" not in answer
    ]
    if len(answers) == 0:
        logging.warning(
            f"Could not parse step answer: {text}. Returning empty list."
        )
        answer = "[]"
    else:
        if len(answers) > 1:
            logging.warning(
                f"Multiple answers found for step answer: {text}. Using the last one."
            )
        answer = answers[-1]
    return answer

def keyword_count_parse_refine_answer(text: str) -> Dict:
    """Parse the keyword counting response from the language model.

    Args:
        text (str): Raw response text from the language model.

    Returns:
        Dict: Parsed frequency dictionary of keywords.
    """

    answer = json_repair.loads(text)
    return answer

def set_intersection_parse_refine_answer(text: str) -> Dict:
    """Parse the set intersection response from the language model.

    Args:
        text (str): Raw response text from the language model.

    Returns:
        Dict: Parsed intersection result.
    """

    answer = json_repair.loads(text)
    return answer