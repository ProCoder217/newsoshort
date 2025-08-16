from summerizer import give_summary
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return str(give_summary("""Opposition parties have voiced strong criticism of Prime Minister Narendra Modi's 
    Independence Day speech, particularly his praise for the Rashtriya Swayamsevak 
    Sangh (RSS). Leaders from the Congress, Trinamool Congress, and AIMIM, among others, 
    accused the Prime Minister of using the occasion for political posturing. The political 
    tussle between Congress leader Rahul Gandhi and the Election Commission of India 
    continues over allegations of "vote theft." Gandhi has refused to sign a sworn 
    declaration backing his claims, stating that the data he cited is from the Election 
    Commission's own records. In other news, the opposition's INDIA bloc is reportedly 
    planning to field a joint candidate for the upcoming Vice-Presidential election. 
    Discussions among the allied parties are said to be underway.""","Politics"))
