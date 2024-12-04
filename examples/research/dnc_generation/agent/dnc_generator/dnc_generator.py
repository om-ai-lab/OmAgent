#  The Implementation of DnC Generation based on the paper 'Li, Bingxuan, et al. Control Large Language Models via Divide and Conquer. EMNLP2024.'

from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.models.llms.schemas import Message, Content
import string
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.models.llms.hf_gpt import HuggingFaceLLM
from omagent_core.models.llms.base import BaseLLMBackend
import re


@registry.register_worker()
class DnCGeneration(BaseWorker, BaseLLMBackend):
    """
    Worker for Divide-and-Conquer text generation.
    Iteratively generates text to include specified keywords and merges results.
    """
    llm: HuggingFaceLLM
    def _run(self, concepts:str, *args, **kwargs):        
        concepts = concepts.split(",")
        response = self._generate_initial_response(concepts)
        rest_set = self._get_rest_concepts(response, concepts)
        record = []
        count = 0
        k = 5

        while count < k and len(rest_set) > 0:
            new_response = self._generate_response(rest_set)
            merged_response = self._merge_responses(response, new_response)
            
            record.append({
                "rest_set": rest_set,
                "old_response": response,
                "new_response": new_response,
                "merged_response": merged_response
            })

            rest_set = self._get_rest_concepts(merged_response, concepts)
            response = merged_response
            count += 1
        
        return {
            "final_response": response,
            "record": record,
            "success": len(rest_set) == 0
        }

    def _generate_initial_response(self, concepts):
        prompt = self._build_prompt(concepts)
        print (prompt)
        return self._call_model(prompt)

    def _generate_response(self, rest_set):
        prompt = self._build_prompt(rest_set)
        return self._call_model(prompt)

    def _merge_responses(self, response1, response2):
        prompt = f"Merge the following two sentences into one:\n'{response1}',\n'{response2}'."
        return self._call_model(prompt)

    def _call_model(self, prompt):
        chat_message = [
            Message(role="user", message_type="text", content=prompt)
        ]
        chat_complete_res = self.llm.generate(records=chat_message)        
        if "responses" in chat_complete_res:
            answer = chat_complete_res["responses"][0]
        else:
            answer = chat_complete_res["choices"][0]["message"]["content"]        
        self.callback.send_answer(self.workflow_instance_id, msg=answer)        
        return answer

    def _simple_get_rest_concepts_(self, response, concepts):        
        response_words = set(response.lower().split())
        return [concept for concept in concepts if concept not in response_words]

    def _get_rest_concepts(self, ans_con, gt_con):
        self.ps = CustomPorterStemmer()  
        
        for punc in string.punctuation:
            ans_con = ans_con.replace(punc, ' ')
        
        ans_word_set = set([self.ps.stem(word_.strip().lower()) for word_ in ans_con.split(' ') if word_ != ''])
        gt_word_set = [self.ps.stem(word_.strip(string.punctuation).strip().lower()) for word_ in gt_con]

        rest_set = []
        for i in range(len(gt_word_set)):
            if gt_word_set[i] not in ans_word_set:
                rest_set.append(gt_con[i])
        
        return rest_set

    def _build_prompt(self, keywords):        
        return f"Generate a sentence including the following keywords: {', '.join(keywords)}."


class CustomPorterStemmer:
    """
    A basic implementation of the Porter Stemming Algorithm.
    """
    
    def __init__(self):
        # Define some common suffixes for stemming
        self.step1a_suffixes = {
            "sses": "ss",
            "ies": "i",
            "ss": "ss",
            "s": ""
        }
        self.step1b_suffixes = ["eed", "ed", "ing"]
        self.vowels = "aeiou"

    def _contains_vowel(self, word):
        """Check if the word contains a vowel."""
        return any(ch in self.vowels for ch in word)

    def _replace_suffix(self, word, suffixes):
        """
        Replace suffixes based on a dictionary or list.
        """
        for suffix, replacement in suffixes.items():
            if word.endswith(suffix):
                return word[: -len(suffix)] + replacement
        return word

    def _step1a(self, word):
        """
        Step 1a: Handle plurals and past participles.
        """
        for suffix, replacement in self.step1a_suffixes.items():
            if word.endswith(suffix):
                return word[: -len(suffix)] + replacement
        return word

    def _step1b(self, word):
        """
        Step 1b: Handle -eed, -ed, and -ing suffixes.
        """
        if word.endswith("eed"):
            if len(word) > 3:
                return word[:-1]  # Remove 'd' from 'eed'
        elif word.endswith("ed"):
            root = word[:-2]
            if self._contains_vowel(root):
                return root
        elif word.endswith("ing"):
            root = word[:-3]
            if self._contains_vowel(root):
                return root
        return word

    def stem(self, word):
        """
        Apply stemming rules to a given word.
        """
        word = word.lower()
        word = self._step1a(word)
        word = self._step1b(word)
        # Additional steps (2, 3, etc.) could be added here for full Porter stemming.
        return word
