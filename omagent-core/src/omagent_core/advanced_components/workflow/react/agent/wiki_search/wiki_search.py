from omagent_core.engine.worker.base import BaseWorker
from omagent_core.utils.registry import registry
from omagent_core.utils.logger import logging
import wikipedia
from pydantic import Field

class WikipediaSearcher:
    """Simple Wikipedia search implementation that mimics DocstoreExplorer"""
    
    def search(self, query: str) -> str:
        """Search Wikipedia and return the page content"""
        try:
            page_content = wikipedia.page(query).content
            return page_content
        except wikipedia.PageError:
            return f"Could not find [{query}]. Similar: {wikipedia.search(query)}"
        except wikipedia.DisambiguationError:
            return f"Could not find [{query}]. Similar: {wikipedia.search(query)}"

@registry.register_worker()
class WikiSearch(BaseWorker):
    """Wiki Search worker for React workflow"""
    
    wiki_searcher: WikipediaSearcher = Field(default_factory=WikipediaSearcher)

    def _run(self, action_output: str, *args, **kwargs):
        """Execute search or lookup based on action output"""
        try:
            # Get context and other states from STM
            state = self.stm(self.workflow_instance_id)
            context = state.get('context', '')
            step_number = self._get_step_number(context)
            
            if 'Search[' in action_output:
                result = self._handle_search(action_output)
            elif 'Lookup[' in action_output:
                result = self._handle_lookup(action_output)
            else:
                result = action_output
                
            # Record observation result
            self.callback.info(
                agent_id=self.workflow_instance_id,
                progress='Observation',
                message=f'Step {step_number}: {result}'
            )
                
            # Update context (only save in STM, not return in response)
            new_context = f"{context}\nObservation {step_number}: {result}"
            
            # Update states including context and step_number
            state.update({
                'context': new_context,
                'step_number': step_number + 1  # Update step number at the end of a round
            })
            
            # Return result with all necessary information
            return {
                'output': result
            }
            
        except Exception as e:
            logging.error(f"Error in WikiSearch: {str(e)}")
            raise

    def _handle_search(self, action_output: str) -> str:
        """Handle Search action"""
        search_term = self._extract_term('Search', action_output)
        if not search_term:
            return action_output
        
        try:
            result = self.wiki_searcher.search(search_term)
            if result:
                result_text = result.strip('\n').strip().replace('\n', '')
                
                # Update state
                self.stm(self.workflow_instance_id).update({
                    'current_document': {'content': result},
                    'lookup_str': '',
                    'lookup_index': 0
                })
                
                return result_text
            else:
                return f"No content found for '{search_term}'"
        except Exception as e:
            return f"Error occurred during search: {str(e)}"

    def _handle_lookup(self, action_output: str) -> str:
        """Handle Lookup action"""
        lookup_term = self._extract_term('Lookup', action_output)
        if not lookup_term:
            return action_output
            
        try:
            # Get state from state manager
            state = self.stm(self.workflow_instance_id)
            current_document = state.get('current_document', {})
            lookup_str = state.get('lookup_str', '')
            lookup_index = state.get('lookup_index', 0)

            if not current_document:
                return "No previous search results available. Please perform a search first."
            
            paragraphs = current_document['content'].split('\n\n')
            
            # Update lookup state
            new_lookup_index = lookup_index
            if lookup_term.lower() != lookup_str:
                new_lookup_str = lookup_term.lower()
                new_lookup_index = 0
            else:
                new_lookup_str = lookup_str
                new_lookup_index += 1
                
            lookups = [p for p in paragraphs if lookup_term.lower() in p.lower()]
            
            if len(lookups) == 0:
                result = "No Results"
            elif new_lookup_index >= len(lookups):
                result = "No More Results"
            else:
                result_prefix = f"(Result {new_lookup_index + 1}/{len(lookups)})"
                result = f"{result_prefix} {lookups[new_lookup_index]}"
                result = result.strip('\n').strip().replace('\n', '')
            
            # Update state
            self.stm(self.workflow_instance_id).update({
                'lookup_str': new_lookup_str,
                'lookup_index': new_lookup_index
            })
            
            return result
            
        except ValueError as ve:
            return str(ve)
        except Exception as e:
            return f"Error occurred during lookup: {str(e)}"

    def _extract_term(self, action_type: str, action_output: str) -> str:
        """Extract term from action output"""
        if f'{action_type}[' in action_output:
            start = action_output.find(f'{action_type}[') + len(action_type) + 1
            end = action_output.find(']', start)
            return action_output[start:end].strip()
        return ""

    def _get_step_number(self, context: str) -> int:
        """Get the current step number from STM"""
        return self.stm(self.workflow_instance_id).get('step_number', 1) 