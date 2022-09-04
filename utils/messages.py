MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE = """
**Your friendly {{game}} announcement!**
Good Morning {{role}}! This week's prompt(s) is ...  

{{#prompts}}
{{id}} ... {{emoji}} {{prompt}}!
{{/prompts}}

**Scores!**
{{#scores}}
**Rank {{id}}** {{emoji}} .... [Score: {{score}}] {{name}} 
{{/scores}}
"""

MESSAGE_APPROVE_ARTWORK = """
Theme: 
{{#prompts}} 
{{emoji}} **{{prompt}}**
{{/prompts}}

Approve this post? {{jumpUrl}}
"""

MESSAGE_WEEKLYPROMPT_WEEK_MESSAGE = """
**[Week {{week}} Prompts]**

Hi everyone! Thank you for the submissions so far (((o(°▽°)o)))

This week’s prompts are: 

{{#prompts}}
{{id}} ... {{emoji}} **{{prompt}}**!
{{/prompts}}

**Note! The template for submissions is:**
```
@Palettober           --- You need to tag the bot
Week: 1               --- Give the week number
Prompt: 2             --- Give the prompt number
```
or...
```
@Palettober
Week: 1
Prompt: 2, 3          --- To target multiple prompts, seperate by space or comma
```
***Note: ***
1. Each person can submit up to 2 works for each prompt! 
2. You can also use more than 1 prompt in your drawing ^o^
3. You can draw towards the prompts of the previous weeks! Just remember to input the correct prompt number.
4. Submissions for this week’s prompts are open till **this Sunday, 2359**.
5. You should receive a receipt within 20 seconds of uploading your artwork. If it does not appear, please try to upload again.

***Looking forward to everyone’s submissions!! ٩(◕‿◕｡)۶ *** 
"""

MESSAGE_WEEKLYPROMPT_WRONG_REQUEST_INPUT =  """
<@{{author}}>
:red_circle: **Wrong format detected!** :red_circle: 

Here is an example:
```
@{{bot_name}}
Week: 1
Prompt: 4 5
```
Try again!
"""

MESSAGE_WEEKLYPROMPT_WRONG_WEEK = """
<@{{author}}> **Wrong prompt was chosen for week {{week}} **

Week {{week}} prompts:
{{#prompts}}
{{id}} ... {{emoji}} **{{prompt}}**!
{{/prompts}}

"""


