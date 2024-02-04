MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE = """
**Scores!**
{{#scores}}
**Rank {{id}}** {{{emoji}}} .... [Score: {{score}}] {{name}} 
{{/scores}}
"""

MESSAGE_APPROVE_ARTWORK = """
Theme: 
{{#prompts}} 
{{{emoji}}} **{{prompt}}**
{{/prompts}}

Approve this post? {{jumpUrl}}
"""

MESSAGE_WEEKLYPROMPT_LAST_WEEK_MESSAGE = """
**[Weekly Prompts Finale]**

Hi everyone! Thank you for your submissions thus far! Hope it has been fun for you  ＼(＾∀＾)メ(＾∀＾)ノ

"""

MESSAGE_WEEKLYPROMPT_WEEK_MESSAGE = """
**[{{period_label}} - Week {{week}} Prompts]**

Hi everyone! Thanks for waiting for the return of our Weekly Prompts, but with the addition of Screencap Redraws!

For weekly prompts, simply create a drawing related to any one of the themes we release this week!
For redraws, you may try recreating the image in your own style, use it as an educational study, swap out the characters entirely, or just make a silly parody! 

Use the screencaps as an easy way to start drawing without having to think too hard 😄

This week’s prompts are: 

{{#prompts}}
{{id}} ... {{{emoji}}} **{{prompt}}**!
{{/prompts}}

And this week's screencap redraw is: 
**{{screencap_img_gdrive_desc}}**
"""

MESSAGE_WEEKLYPROMPT_WEEK_MESSAGE_2 = """

**Note! The template for submissions is:**
```
@{{bot_name}}         --- You need to tag the bot
Week: 1               --- Give the week number
Prompt: 2             --- Give the prompt number
Title: blablabla      --- (Optional) Write something about your artwork
```
or...
```
@{{bot_name}}
Week: 1
Prompt: 2, 3          --- To target multiple prompts, seperate by space or comma
Title: blablabla      
```
**Note that the bot needs to be tagged (Blue Highlight); Plaintext may not work!**
***Note: ***
1. Each person can submit up to 2 works for each week! 
2. You can also use more than 1 prompt in your drawing ^o^
3. Submissions for this week’s prompts are open till **this Sunday, 2359**, to be counted towards this week's scoreboard.
4. You should receive a receipt within 20 seconds of uploading your artwork. If it does not appear, please try to upload again.
5. Your artwork will be subjected to approval by an Exco member, to ensure fairness in crediting of scores. Only after a approval will you get a point!

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
Edit your message and try again!
"""

MESSAGE_WEEKLYPROMPT_WRONG_WEEK = """
<@{{author}}> **Wrong prompt was chosen for week {{week}} **

Week {{week}} prompts:
{{#prompts}}
{{id}} ... {{{emoji}}} **{{prompt}}**!
{{/prompts}}

"""

MESSAGE_WEEKLYPROMPT_BLOCKED_WEEK = ":pencil2: :book: This week is break week! Focus on your exams or submissions :muscle: :muscle:"


