MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE = """
Your friendly {{game}} announcement!
Good Morning {{role}}! Today's prompt(s) is ...  

{{#prompts}}
{{id}} ... {{emoji}} {{prompt}}!
{{/prompts}}

Scores!
{{#scores}}
Rank {{id}} {{emoji}} .... [Score: {{score}}] {{name}} 
{{/scores}}
"""

MESSAGE_APPROVE_ARTWORK = """
Theme: 
{{#prompts}} 
{{emoji}} {{prompt}}
{{/prompts}}. 

Approve this post? {{jumpUrl}}
"""

