from typing import List
from pydantic import BaseModel, Field


class CoTExample( BaseModel ):
    demo: str = ''

    def check_inpout( self, examples: List[ dict ] ) -> bool:
        """
        Checks if the input is a list of dictionaries with specific keys.
        Args:
            examples (List[dict]): A list of dictionaries to be checked.
        Returns:
            bool: True if the input is a list of dictionaries and each dictionary
                    contains exactly the keys 'q', 'r', and 'a'. False otherwise.
        """
        if isinstance( examples, list ) and all(
            isinstance( example, dict ) and
            set( example.keys() ) == { 'q', 'r', 'a' } for example in examples
        ):
            return True
        return False

    def create_examples( self, cot_examples: List[ dict ] ) -> str:
        """
        Creates example strings from a list of dictionaries and appends them to the demo attribute.
        Args:
            examples (List[dict]): A list of dictionaries, each containing keys 'q' for question, 
                                   'a' for answer, and 'r' for the result.
        Returns:
            str: The updated demo string with appended examples.
        """
        if self.check_inpout( cot_examples ):
            demos = [f"Q: {example['q']}\nA: {example['r']} The answer is {example['a']}." for example in cot_examples]
            self.demo = '\n\n'.join( demos )
        return self.demo
