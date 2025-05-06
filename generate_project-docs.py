from zindango_api_call import ZindangoLLM

zindango = ZindangoLLM(model_name="mathzenepoch3")
idea = "Uber for flying cars."
prfaq = zindango.generate_prfaq_md(idea)
functional_doc = zindango.generate_functional_doc(idea, prfaq)
design_doc = zindango.generate_design_doc(idea, prfaq, functional_doc)
architecture_doc = zindango.generate_architecture_doc(idea, prfaq, functional_doc, design_doc)
user_stories = zindango.generate_user_stories_and_tasks(idea, prfaq, functional_doc, design_doc, architecture_doc)
zindango.generate_vibe_coding_prompts(user_stories)
zindango.generate_devplan_md(idea, prfaq, functional_doc, design_doc, architecture_doc, user_stories)