grammar lc;

program: (macro | terme);

macro: (MACRO_NAME|OPERATOR) ('≡'| '=') terme     #mac
    | MACRO_NAME ' ' macro                      #usage
    | MACRO_NAME OPERATOR macro                 #infix
    | MACRO_NAME                               #usage1
    ;

terme: Lletra                        #valor    
    | terme terme                  #aplicacio
    | ('\\' | 'λ') Lletra '.' terme  #abstraccio
    | '(' terme ')'                 #parentesis
    ;

Lletra: [a-z] [a-z]?;
MACRO_NAME: [A-Z0-9]+;
OPERATOR: [!"#$%&'()*+,-./:<=>?@{|}~];
WS: [ \t\r\n]+ -> skip;


