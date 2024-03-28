from __future__ import annotations
from typing import Union
from dataclasses import dataclass
from antlr4 import *
from lcLexer import lcLexer
from lcParser import lcParser
from lcVisitor import lcVisitor
import string
import logging
import pydot
import copy

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
# set higher logging level for httpx to avoid all GET and POST requests
# being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@dataclass
class Lletra:
    llet: chr


@dataclass
class Abstraccio:
    llet: chr
    t: Terme


@dataclass
class Aplicacio:
    tesq: Terme
    tdre: Terme


# python 3.8.10 no inclou el operand '|'
Terme = Union[Lletra, Aplicacio, Abstraccio]

abecedari = list(string.ascii_lowercase)

macros = {}


# variables potencialment lliures
def variables_pot_lliures(term: Terme) -> list[chr]:
    if isinstance(term, Lletra):
        return [term.llet]
    elif isinstance(term, Aplicacio):
        return variables_pot_lliures(
            term.tesq) + variables_pot_lliures(term.tdre)
    elif isinstance(term, Abstraccio):
        return variables_pot_lliures(term.t)

# variables lligades


def variables_llig(term: Terme) -> list[chr]:
    if isinstance(term, Lletra):
        return []
    elif isinstance(term, Aplicacio):
        return variables_llig(term.tesq) + variables_llig(term.tdre)
    elif isinstance(term, Abstraccio):
        return [term.llet] + variables_llig(term.t)


def escribir_arbre(arbre: Terme) -> str:
    if isinstance(arbre, Lletra):
        return arbre.llet
    elif isinstance(arbre, Aplicacio):
        tesq = escribir_arbre(arbre.tesq)
        tdre = escribir_arbre(arbre.tdre)
        return f"({tesq}{tdre})"
    elif isinstance(arbre, Abstraccio):
        llet = arbre.llet
        t = escribir_arbre(arbre.t)
        return f"(λ{llet}.{t})"


def imatge_arbre(arbre: Terme):
    contador = 0

    def recorrer_arbre(node, graf, var_lligades):
        nonlocal contador

        if isinstance(node, Lletra):

            node_graf = pydot.Node(f"node_{contador}", label=node.llet)
            if node.llet in var_lligades:
                graf.add_edge(pydot.Edge(
                    node_graf, var_lligades[node.llet], style="dashed"))
            contador += 1
            graf.add_node(node_graf)

            return node_graf

        elif isinstance(node, Aplicacio):
            node_graf = pydot.Node(f"node_{contador}", label="@")
            contador += 1
            graf.add_node(node_graf)
            # fem una deepcopy perque a la recursivitat no es solapin els mapes
            aux = copy.deepcopy(var_lligades)
            tesq_graf = recorrer_arbre(node.tesq, graf, var_lligades)
            tdre_graf = recorrer_arbre(node.tdre, graf, aux)

            graf.add_edge(pydot.Edge(node_graf, tesq_graf))
            graf.add_edge(pydot.Edge(node_graf, tdre_graf))

            return node_graf

        elif isinstance(node, Abstraccio):
            node_graf = pydot.Node(f"node_{contador}", label=f"λ{node.llet}")
            var_lligades[node.llet] = f"node_{contador}"
            contador += 1
            graf.add_node(node_graf)
            t_graf = recorrer_arbre(node.t, graf, var_lligades)
            graf.add_edge(pydot.Edge(node_graf, t_graf))

            return node_graf

    graf = pydot.Dot(graph_type="digraph")
    recorrer_arbre(arbre, graf, {})
    return graf


# aquesta funcio fa un sol pas de reduccio beta, però pot fer diverses alfa reduccions si es necessari
# retorna el terme a imprimir pero també el llistat de reduccions en forma
# de llista per a poder ser enviat per telegram
def pas_reduccio(term: Terme) -> list[Terme, list[str]]:
    global abecedari
    l = []
    if isinstance(term, Lletra):
        return [term, l]

    if isinstance(term, Aplicacio):
        if isinstance(term.tesq, Abstraccio):
            # primer emmagatzemem aquelles variables potencialment lliures
            v = set(variables_pot_lliures(term.tdre))
            # a continuacio aquelles lligades
            v_llig_dret = set(variables_llig(term.tdre))
            v_lliu_dre = []
            # fem la resta de conjunts per obtenir les variables lliures
            v_lliu_dre = [x for x in v if x not in v_llig_dret]
            v_llig_esq = set(variables_llig(term.tesq.t) + [term.tesq.llet])
            # actualitzem el abecedari per futures renanomenacions
            abecedari = [
                x for x in abecedari if x not in v_lliu_dre and x not in v_llig_esq]
            elem_comu = list(set(v_lliu_dre) & set(v_llig_esq))

            if len(elem_comu) > 0:
                conv_alfa = term.tesq
                for i in elem_comu:
                    print(f"α-conversió {i} → {abecedari[0]}:")
                    l.append(f"α-conversió {i} → {abecedari[0]}:")
                    conv_alfa = substituir(conv_alfa, i, Lletra(abecedari[0]))
                    abecedari.pop(0)

                print(f"{escribir_arbre(term.tesq)} → {escribir_arbre(conv_alfa)}")
                l.append(
                    f"{escribir_arbre(term.tesq)} → {escribir_arbre(conv_alfa)}")
                return [Aplicacio(conv_alfa, term.tdre), l]

            else:
                print("β-reducció:")
                red = substituir(term.tesq.t, term.tesq.llet, term.tdre)
                print(f"{escribir_arbre(term)} → {escribir_arbre(red)}")
                l.append(f"{escribir_arbre(term)} → β → {escribir_arbre(red)}")
                if (red == term):
                    print("Crides recursives infinites! No es pot resoldre")
                    l.append("Crides recursives infinites! No es pot resoldre")
                    return [Lletra(llet=''), l]
                else:
                    return [red, l]

        else:
            [tesq_reduit, l] = pas_reduccio(term.tesq)
            if (tesq_reduit != term.tesq):
                return [Aplicacio(tesq_reduit, term.tdre), l]
            else:
                [tdre_reduit, l] = pas_reduccio(term.tdre)
                return [Aplicacio(term.tesq, tdre_reduit), l]

    if isinstance(term, Abstraccio):
        [t_reduit, l] = pas_reduccio(term.t)
        return [Abstraccio(term.llet, t_reduit), l]


def substituir(term: Terme, lletra: chr, reemp: Terme) -> Terme:

    if isinstance(term, Lletra):
        if lletra == term.llet:
            return reemp
        else:
            return term

    if isinstance(term, Aplicacio):
        tesq_reemp = substituir(term.tesq, lletra, reemp)
        tdre_reemp = substituir(term.tdre, lletra, reemp)
        return Aplicacio(tesq_reemp, tdre_reemp)

    if isinstance(term, Abstraccio):

        if term.llet == lletra:
            t_reemp = substituir(term.t, lletra, reemp)
            return Abstraccio(reemp.llet, t_reemp)

        else:
            t_reemp = substituir(term.t, lletra, reemp)
            return Abstraccio(term.llet, t_reemp)


class TreeVisitor(lcVisitor):

    def visitAplicacio(self, ctx):
        [esq, dre] = list(ctx.getChildren())
        arbre = Aplicacio(tesq=self.visit(esq), tdre=self.visit(dre))
        return arbre

    def visitAbstraccio(self, ctx):
        [_, l, _, terme] = list(ctx.getChildren())

        s = l.getText()
        if len(s) == 1:
            arbre = Abstraccio(llet=s, t=self.visit(terme))
        else:
            arbre = Abstraccio(
                llet=s[0], t=Abstraccio(
                    s[1], self.visit(terme)))
        return arbre

    def visitParentesis(self, ctx):
        [_, t, _] = list(ctx.getChildren())
        return self.visit(t)

    def visitValor(self, ctx):
        [valor] = list(ctx.getChildren())

        s = valor.getText()
        if len(s) == 1:
            arbre = Lletra(llet=s)
        else:
            arbre = Aplicacio(tesq=Lletra(llet=s[0]), tdre=Lletra(llet=s[1]))
        return arbre

    def visitMac(self, ctx):
        [ide, _, t] = list(ctx.getChildren())
        arbre = self.visit(t)
        macros[ide.getText()] = arbre

        for macro, tree in macros.items():
            print(f"{macro} ≡ {escribir_arbre(tree)}")

        return None

    def visitUsage(self, ctx):
        [m, _, altre] = list(ctx.getChildren())
        mac = m.getText()
        if mac not in macros:
            print(f"Error: Macro '{mac}' no definida.")
            return None

        return Aplicacio(macros[mac], self.visit(altre))

    def visitInfix(self, ctx):
        [m, inf, altre] = list(ctx.getChildren())
        mac = m.getText()
        simb = inf.getText()
        if mac not in macros:
            print(f"Error: Macro '{mac}' no definida.")
            return None

        if simb not in macros:
            print(f"Error: Macro '{simb}' no definida.")
            return None

        return Aplicacio(
            (Aplicacio(
                macros[simb],
                macros[mac])),
            self.visit(altre))

    def visitUsage1(self, ctx):
        [ide] = list(ctx.getChildren())

        prim = ide.getText()
        if prim not in macros:
            print(f"Error: Macro '{prim}' no definida.")
            return None

        return macros[prim]


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text("AChurchBot!")
    await update.message.reply_html(
        rf"Benvingut {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("/start\n/author\n/help\n/macros\n/versions\n/capabilities\n/sources\nExpressió λ-càlcul")


async def autor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /autor is issued."""
    await update.message.reply_text("AChurchBot!\n@ Miquel Muñoz García-Ramos, 2023")


async def macros_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /macro is issued."""
    if (len(macros) == 0):
        await update.message.reply_text("Encara no hi ha macros definides!")
    else:
        for macro, tree in macros.items():
            await update.message.reply_text(f"{macro} ≡ {escribir_arbre(tree)}")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    input_stream = InputStream(update.message.text)
    lexer = lcLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = lcParser(token_stream)
    tree = parser.program()
    if parser.getNumberOfSyntaxErrors() == 0:
        visitor = TreeVisitor()
        arbre = visitor.visit(tree)
        if arbre is not None:
            print("Arbre:")
            print(escribir_arbre(arbre))
            await update.message.reply_text(f"Arbre:\n{escribir_arbre(arbre)}")
            image = imatge_arbre(arbre)
            image.write_png("output.png")
            await update.message.reply_photo(photo=open("output.png", "rb"))
            [resultat, l] = pas_reduccio(arbre)
            for elem in l:
                await update.message.reply_text(elem)

            while resultat != arbre:
                arbre = resultat
                [resultat, l] = pas_reduccio(arbre)
                for elem in l:
                    await update.message.reply_text(elem)

            print("Resultat:")
            if escribir_arbre(resultat) == "":
                print("Nothing")
                await update.message.reply_text("Resultat:\nNothing")
            else:
                print(escribir_arbre(resultat))
                await update.message.reply_text(f"Resultat:\n{escribir_arbre(resultat)}")
                image = imatge_arbre(resultat)
                image.write_png("output.png")
                await update.message.reply_photo(photo=open("output.png", "rb"))

        global abecedari
        abecedari = list(string.ascii_lowercase)
        print("---------------------------------------")
    else:
        print(parser.getNumberOfSyntaxErrors(), 'errors de sintaxi.')
        await update.message.reply_text(str(parser.getNumberOfSyntaxErrors()) + " errors de sintaxi.")
        print(tree.toStringTree(recog=parser))
        await update.message.reply_text(tree.toStringTree(recog=parser))


async def versions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Programat utilitzant Python 3.8.10 i ANTLR 4.13.0.\nTambé, les llibreries python-telegram-bot 20.3 i pydot 1.4.2.")


async def capabilities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Aquest programa és capaç d'interpretar i avaluar expressions en λ-càlcul (els caràcters 'λ' i '\\' són equivalents). \nTambé les converteix en arbres semàntics que es mostren en parèntesis i imatges on s'observen les dependències de les variables lligades en línies discontínues. A més, permet l'ús i la definició de macros utilitzant '=' o '≡' (opcionalment, en notació infixa). ")


async def sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("- Enunciat: https://gebakx.github.io/lp-achurch-23/\n- Alonzo Church - Wikipedia: https://en.wikipedia.org/wiki/Alonzo_Church\n- ANTLR en Python: https://gebakx.github.io/Python3/compiladors.html#1\n- Fonaments: λ-càlcul: https://jpetit.jutge.org/lp/03-lambda-calcul.html\n- Lambda calculus - Lambda Calculus: http://www-cs-students.stanford.edu/~blynn/lambda/\n- Lambda-Calculus Evaluator: https://www.cl.cam.ac.uk/~rmk35/lambda_calculus/lambda_calculus.html\n- Lambda Calculus Interpreter: https://jacksongl.github.io/files/demo/lambda/index.htm\n- python-telegram-bot: https://docs.python-telegram-bot.org/en/stable/\n- pydot: https://github.com/pydot/pydot")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(
        "6173258582:AAGOt8_pZ8pWwzTX9rq6J_CchcYOKkc_AaU").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("author", autor))
    application.add_handler(CommandHandler("macros", macros_handler))
    application.add_handler(CommandHandler("versions", versions))
    application.add_handler(CommandHandler("capabilities", capabilities))
    application.add_handler(CommandHandler("sources", sources))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
