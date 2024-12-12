from omagent_core.agents_lib.outfit_recommendation.outfit_recommendation.outfit_recommendation import OutfitRecommendation
from omagent_core.agents_lib.outfit_recommendation.weather_decider.weather_decider import WeatherDecider
from omagent_core.agents_lib.outfit_recommendation.weather_searcher.weather_searcher import WeatherSearcher
from omagent_core.agents_lib.simple_vqa.simple_vqa_agent import InputInterface

from omagent_core.lite_engine.task import Task
from omagent_core.lite_engine.workflow import Workflow
from omagent_core.models.llms.hf_gpt import HuggingFaceLLM
from omagent_core.models.llms.openai_gpt import OpenaiGPTLLM
from omagent_core.tool_system.manager import ToolManager
from omagent_core.tool_system.tools.web_search.search import WebSearch

from omagent_core.utils.container import container
from omagent_core.utils.logger import logging


class OutFitRec:
    def __init__(self,api_key):
        llm = OpenaiGPTLLM(api_key=api_key)        
        web_search_tool = WebSearch(bing_api_key="bing_api", llm=llm)    
        tool_manager = ToolManager(name="WebSearch", tools=[web_search_tool], llm=llm)

        self.input_interface = InputInterface()
        self.outfit = OutfitRecommendation(llm=llm)
        self.weather_decider = WeatherDecider(llm=llm)
        self.weather_search = WeatherSearcher(llm=llm, tool_manager=tool_manager)
        

    def run(self, inputs):
        task1 = Task(name='InputInterface', func=self.input_interface, inputs=inputs)
        # 2. Weather decision logic based on user input
        #print ("task1.output",task1.output)
        task2 = Task(name='WeatherDecider', func=self.weather_decider , inputs=task1.output)
        # 3. Weather information retrieval        
        task3 = Task(name='WeatherSearcher', func=self.weather_search, inputs=task1.output)
        # 4. Final outfit recommendation generation
        task4 = Task(name='OutfitRecommendation', func=self.outfit, inputs=task3.output)
        workflow = Workflow(name='example_workflow')        
        workflow >> task1 >> task2 >> {0 : task3} >> task4
        workflow.execute()        
        return task4.output()



if __name__ == "__main__":
    logging.init_logger("omagent", "omagent", level="INFO")
    container.register_stm("RedisSTM")    
    user_input = {
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "data": "recommend style?"
                },
                {
                    "type": "image_url",
                    "data": "demo.jpg"
                }
            ]
        }
    ]
}
    o = OutFitRec(api_key="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")
    final = o.run(user_input)
    print (final)