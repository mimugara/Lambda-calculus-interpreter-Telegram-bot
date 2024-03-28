# Pràctica de Python i Compilació

---

**Intèrpret de λ-càlcul AChurch**

Aquest projecte és un intèrpret de λ-càlcul anomenat AChurch. 
S'ha desenvolupat a l'assignatura Llenguatges de Programació (LP) de la Facultat d'Informàtica de Barcelona (FIB - UPC)
durant l'edició 2022-2023 Q2.

Autor: Miquel Muñoz García-ramos `miquel.munoz.garcia-ramos@estudiantat.upc.edu`

---

### Versions

Programat utilitzant Python 3.8.10 i ANTLR 4.13.0.
També, les llibreries python-telegram-bot 20.3 i pydot 1.4.2.

---

### Funcionament

Compilar la gramàtica i generar la classe base del visitador (lcVisitor.py) a més dels altres arxius necessaris:

```bash
antlr4 -Dlanguage=Python3 -no-listener -visitor lc.g4    # antlr en MacOS
```
Per executar el programa:

```bash
python3 achurch.py
```

Per a parar l'execució es pot polsar Ctrl+C.

L’intèrpret AChurch funciona a Telegram via la llibreria python-telegram-bot. Per entrar-hi s'ha d'entrar a https://t.me/AChurchMiquelMunozBot utilitzant el següent **token** per accedir al HTTP API: **6173258582:AAGOt8_pZ8pWwzTX9rq6J_CchcYOKkc_AaU**. Tot i així, si es vol crear un bot nou a Telegram cal seguir els passos descrits a https://docs.python-telegram-bot.org/en/stable/. En aquest cas, s'ha de substituir el nou token a l'arxiu achurch.py.

El codi inclou una implementació de patrons de visitadors per travessar l'arbre de sintaxi abstracte generat pel ANTLR *parser*. A més, defineix diverses classes de dades com Lletra, Abstraccio i Aplicacio, que representen diferents components de les expressions de lambda càlcul. També inclou funcions per realitzar passos de reducció, la substitució de variables o per generar les imatges dels grafs. La reducció es fa seguint l’estratègia d’ordre de reducció normal.

---

### Capacitats i ampliacions

Aquest programa és capaç d'interpretar i avaluar expressions en λ-càlcul (els caràcters 'λ' i '\\' són equivalents). 

També les converteix en arbres semàntics que es mostren en parèntesis i imatges on s'observen les dependències de les variables lligades en línies discontínues. A més, permet l'ús (opcionalment, en notació infixa) i la definició de macros utilitzant '=' o '≡'.

El bot admet les comandes /start, /help, /author, /macros i s'ha ampliat amb /versions /capabilities i /sources.

---

### Fonts 

- Enunciat: https://gebakx.github.io/lp-achurch-23/
  
- Alonzo Church - Wikipedia: https://en.wikipedia.org/wiki/Alonzo_Church

- ANTLR en Python: https://gebakx.github.io/Python3/compiladors.html#1

- Fonaments: λ-càlcul: https://jpetit.jutge.org/lp/03-lambda-calcul.html

- Lambda calculus - Lambda Calculus: http://www-cs-students.stanford.edu/~blynn/lambda/

- Lambda-Calculus Evaluator: https://www.cl.cam.ac.uk/~rmk35/lambda_calculus/lambda_calculus.html

- Lambda Calculus Interpreter: https://jacksongl.github.io/files/demo/lambda/index.htm

- python-telegram-bot: https://docs.python-telegram-bot.org/en/stable/

- pydot: https://github.com/pydot/pydot





