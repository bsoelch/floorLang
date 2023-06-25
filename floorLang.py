import re
from fractions import Fraction
import math
import argparse
import sys

class Bracket:
  def __init__(self,bracket):
    self.brackets=['()','()','[]','[]','{}','{}'][['(',')','[',']','{','}'].index(bracket)]
    self.isOpen=bracket in ['(','[','{']

  def __repr__(self):
    if self.isOpen:
      return self.brackets[0]
    else:
      return self.brackets[1]

class Expression:
  pass

class Number(Expression):
  def __init__(self,value):
    self.value=value

  def __str__(self):
    return str(self.value)

  def __repr__(self):
    return str(self.value)

  def evaluate(self,args,functions):
    return Fraction(self.value)

class Argument(Expression):
  def __init__(self,name):
    self.name=name

  def __str__(self):
    return self.name

  def __repr__(self):
    return self.name

  def __eq__(self,other):
    if not isinstance(other,Argument):
      return False
    return self.name==other.name

  def __hash__(self):
    return hash(self.name)

  def evaluate(self,args,functions):
    val=args.get(self)
    if val is None:
      raise Exception("missing argument: "+self.name);
    elif isinstance(val,Expression):
      val=val.evaluate(args,functions)
    return val


class Operator(Expression):
  def __init__(self,opType,left=None,right=None):
    self.opType=opType;
    self.left=left;
    self.right=right;

  def __str__(self):
    if self.left is None:
      left="?"
    else:
      left=repr(self.left)
    if self.right is None:
      right="?"
    else:
      right=repr(self.right)
    return left+self.opType+right;

  def __repr__(self):
    return "("+str(self)+")";

  def evaluate(self,args,functions):
    l=self.left.evaluate(args,functions);
    if l==0 and (self.opType=="*"):
      return l
    if l==1 and (self.opType=="^"):
      return l
    r=self.right.evaluate(args,functions)
    if self.opType=="+":
      return l+r
    if self.opType=="-":
      return l-r
    if self.opType=="*":
      return l*r
    if self.opType=="/":
      if r==0: return 0;
      return l/r
    if self.opType=="^":
      if l==0 and r<0: return 0;
      return l**math.floor(r)

class FunctionCall(Expression):
  def __init__(self,name,args=[]):
    self.name=name
    self.repeat=None
    self.hasArgs=(len(args)==0)
    for e in args:
      if e!=None:
        self.hasArgs=True
    self.args=args

  def __repr__(self):
    exp=""
    if self.repeat!=None:
      exp="^"+repr(self.repeat)
    return self.name+exp+"("+str(self.args)[1:-1]+")";

  def evaluate(self,args,functions):
    oldArgs=args
    args=dict(args)
    f=functions.get(self.name)
    if f is None:
      raise Exception(f"cannot resolve function {self.name}")
    if len(f.args)!=len(self.args):
      raise Exception(f"function {self.name} has the wrong number of arguments, expected {len(self.args)} got {len(f.args)}")
    for i in range(0,len(f.args)):
      args[f.args[i]]=self.args[i].evaluate(oldArgs,functions)
    if self.repeat is None:
      return f.evaluate(args,functions)
    if len(self.args)==0:
      raise Exception("can only repeat functions that take arguments");
    rep=math.floor(self.repeat.evaluate(oldArgs,functions))
    for _ in range(0,rep):
      args[f.args[0]]=f.evaluate(args,functions)
    return args[f.args[0]]

class Function:
  def __init__(self,name,args,body):
    self.name=name
    self.args=args
    self.body=body

  def __repr__(self):
    return self.name+": "+str(self.args)[1:-1].replace(",","")+" -> "+str(self.body);

  def evaluate(self,args,functions):
    return self.body.evaluate(args,functions)

class BuiltinFunction(Function):
  def __init__(self,name,args,f):
    self.name=name
    self.args=args
    self.f=f

  def __repr__(self):
    return self.name+": "+str(self.args)[1:-1].replace(",","")+" -> ...";

  def evaluate(self,args,functions):
    mArgs=[]
    for a in self.args:
      mArgs.append(args[a]) ## XXX? error message for missing argument
    return self.f(*mArgs)

def checkExpr(elt):
  if not isinstance(elt,Expression):
    raise Exception("Syntax error: expected expression got "+str(type(elt))+" "+str(elt))
  if isinstance(elt,Operator) and (elt.left is None or elt.right is None):
    raise Exception("Syntax error: expected expression got incomplete operator "+str(elt))
  if isinstance(elt,FunctionCall) and not elt.hasArgs:
    raise Exception("Syntax error: expected expression got incomplete function call "+str(elt))
  return elt

def isExpr(elt):
  if not isinstance(elt,Expression):
    return False
  if isinstance(elt,Operator) and (elt.left is None or elt.right is None):
    return False
  if isinstance(elt,FunctionCall) and not elt.hasArgs:
    return False
  return True

def parseExpression(elts):
  i0=0
  openBrackets=0
  openType=None
  for i in range(0,len(elts)):
    if isinstance(elts[i],Bracket):
      if openBrackets==0:
        if not elts[i].isOpen:
          raise Exception("Syntax error: unexpected open bracket") ## XXX? better error messages
        openType=elts[i].brackets
        openBrackets=1
        i0=i
        continue
      if openBrackets>0 and elts[i].brackets==openType:
        if elts[i].isOpen:
          openBrackets+=1
        else:
          openBrackets-=1
        if openBrackets==0:
          elts[i0]=parseExpression(elts[i0+1:i])
          elts[i0+1:i+1]=[None]*(i-i0) ## pad with None to keep size the same
  if openBrackets>0:
      raise Exception("Syntax error: missing closing bracket" )
  elts=list(filter (lambda a: a != None, elts)) ## remove None elements
  for i in range(1,len(elts)): ## square and cube operators
    if isinstance(elts[i],Operator) and elts[i].opType=="^" and elts[i].left is None and elts[i].right!=None:
      if isinstance(elts[i-1],FunctionCall) and elts[i-1].repeat is None and not elts[i-1].hasArgs: ## XXX allow procedures with multiple exponents
        elts[i-1].repeat=elts[i].right
        elts[i]=elts[i-1]
      else:
        elts[i].left=checkExpr(elts[i-1])
      elts[i-1]=None
  elts=list(filter (lambda a: a != None, elts)) ## remove None elements
  i=len(elts)-1
  while i>=0: ## function calls and ^ operator
    if isinstance(elts[i],FunctionCall) and not elts[i].hasArgs:
      n=len(elts[i].args)
      i0=i+1
      i1=i0
      if i0<len(elts) and elts[i].repeat is None and isinstance(elts[i0],Operator) and elts[i0].opType=="^" and elts[i0].left is None:
        elts[i].repeat=checkExpr(elts[i0+1])
        i1=i0+2
      if i1+n>len(elts):
        raise Exception("Not enough arguments for function "+elts[i].name)
      for e in range(0,n):
        elts[i].args[e]=checkExpr(elts[i1+e])
      elts[i].hasArgs=True
      elts[i0:i1+n]=[]
    elif (isinstance(elts[i],Operator) and (elts[i].opType=="+" or elts[i].opType=="-") and elts[i].left is None
        and (i==0 or (isinstance(elts[i-1],Operator) and elts[i-1].right is None) or (isinstance(elts[i-1],FunctionCall) and not elts[i-1].hasArgs))
        and (i+1<len(elts) and not (isinstance(elts[i+1],Operator) and elts[i+1].left is None))):##unary minus
      elts[i]=FunctionCall(elts[i].opType,[checkExpr(elts[i+1])])
      elts[i+1:i+2]=[]
      pass
    i-=1
  i=len(elts)-1
  while i>0: ## ^ operator
    if isinstance(elts[i],Operator) and elts[i].opType=="^" and elts[i].left is None:
      elts[i].left=checkExpr(elts[i-1])
      elts[i].right=checkExpr(elts[i+1])
      elts[i-1]=elts[i]
      elts[i:i+2]=[]
    i-=1
  i=1
  while i<len(elts): ## multiplication and division
    if i+1<len(elts) and isinstance(elts[i],Operator) and elts[i].left is None and (elts[i].opType=="*" or elts[i].opType=="/"):
      elts[i].left=checkExpr(elts[i-1])
      elts[i].right=checkExpr(elts[i+1])
      elts[i-1]=elts[i]
      elts[i:i+2]=[]
      i-=1
    elif isExpr(elts[i-1]) and isExpr(elts[i]):
      mult=Operator("*",checkExpr(elts[i-1]),checkExpr(elts[i]))
      elts[i-1]=mult
      elts[i:i+1]=[]
      i-=1
    i+=1
  i=1
  while i+1<len(elts): ## addition and subtraction
    if isinstance(elts[i],Operator) and elts[i].left is None and (elts[i].opType=="+" or elts[i].opType=="-"):
      elts[i].left=checkExpr(elts[i-1])
      elts[i].right=checkExpr(elts[i+1])
      elts[i-1]=elts[i]
      elts[i:i+2]=[]
      i-=1
    i+=1
  if len(elts)!=1:
    raise Exception("could not parse expression:",elts)
  return elts[0]

IDENTIFER_REGEX="[a-zA-Z][a-zA-Z_0-9]*"

def parseLine(line,functions):
  line=line.strip();
  if len(line)==0 or line[0]=='#':
    return
  parts=re.split("(->|"+IDENTIFER_REGEX+":|[\\+\\-*/^ \t\\(\\)\\[\\]\\{\\}²³])",line);
  parts=list(filter(lambda a: len(a)>0, map(lambda a:a.strip(),parts)))
  if len(parts)==0:
    return
  declare=None
  myArgs=dict()
  if parts[0][-1]==':':
    declare=parts[0][:-1]
    if not re.match(IDENTIFER_REGEX+"$",declare):
      raise Exception("invalid name for function: "+declare)
    i=1
    while i<len(parts) and parts[i]!='->':
      if len(parts[i])==0:
        continue
      if not re.match(IDENTIFER_REGEX+"$",parts[i]):
        raise Exception("invalid name for function argument: "+parts[i])
      if parts[i] in myArgs:
        raise Exception("duplicate name for function argument: "+parts[i])
      myArgs[parts[i]]=Argument(parts[i])
      i+=1
    if i==len(parts):
      raise Exception("unexpected end of function declaration, expected ->")
    parts=parts[i+1:]
  elements=[]
  for x in parts:
    x=x.strip()
    if len(x)==0:
      continue
    if x in ['+','-','*','/','^']:
      elements.append(Operator(x))
      continue
    if x =='²':
      elements.append(Operator("^",None,Number(2)))
      continue
    if x =='³':
      elements.append(Operator("^",None,Number(3)))
      continue
    if x in ['(',')','[',']','{','}']:
      elements.append(Bracket(x))
      continue
    x=re.split("(^[0-9]+)",x);
    x=list(filter(lambda a: len(a)>0, map(lambda a:a.strip(),x)))
    for y in x:
      y=y.strip()
      if len(y)==0:
        continue
      if re.match(r"[0-9]+$",y):
        elements.append(Number(int(y)))
      elif y in myArgs:
        elements.append(myArgs[y])
      elif y in functions:
        elements.append(FunctionCall(y,len(functions[y].args)*[None]))
      else:
        raise Exception("unknown name: "+y)
  expr=parseExpression(elements)
  if declare!=None:
    functions[declare]=Function(declare,list(myArgs.values()),expr) ## myArgs.values is in the same order the arguments appeared in source code
    return
  print(expr)


def parseParam(val,mode):
  if mode==None:
    return int(val.strip(),10)
  if mode=="hex":
    return int(val.strip(),16)
  if mode=="bin":
    return int(val.strip(),2)
  if mode=="str":
    v=0
    shift=0
    for b in val.encode('utf-8'):
      v=(b<<shift)|v
      shift+=8
    return v
  raise Exception(f"unknown input mode: {mode}")

def valueToString(val,mode):
  if mode==None:
    return str(val)
  if mode=="hex":
    if val.denominator == 1:
      return hex(val.numerator)
    return hex(val.numerator)+"/"+hex(val.denominator)
  if mode=="bin":
    if val.denominator == 1:
      return bin(val.numerator)
    return bin(val.numerator)+"/"+bin(val.denominator)
  if mode=="str":
    b=b""
    val=abs(math.floor(val))
    while val!=0:
      b+=(val&0xff).to_bytes(1)
      val>>=8
    return b.decode('utf-8', 'ignore')
  raise Exception(f"unknown output mode: {mode}")

def main():
  parser=argparse.ArgumentParser()
  parser.add_argument('-f', '--src')
  parser.add_argument('-s', dest='in_mode',action='store_const',const="str")
  parser.add_argument('-S', dest='out_mode',action='store_const',const="str")
  parser.add_argument('-x', dest='in_mode',action='store_const',const="hex")
  parser.add_argument('-X', dest='out_mode',action='store_const',const="hex")
  parser.add_argument('-b', dest='in_mode',action='store_const',const="bin")
  parser.add_argument('-B', dest='out_mode',action='store_const',const="bin")
  parser.add_argument('-v', dest='verbose',action='store_true')
  parser.add_argument('params', nargs='*')
  args=parser.parse_args()
  params=[parseParam(p,args.in_mode) for p in args.params]
  src=args.src
  if src is None:
    src="./test.txt"
  with open(src, encoding="utf-8") as f:
      code = f.read()
  functions=dict()
  functions["floor"]=BuiltinFunction("floor",[Argument("x")],lambda x:math.floor(x))
  functions["+"]=BuiltinFunction("+",[Argument("x")],lambda x:x)
  functions["-"]=BuiltinFunction("-",[Argument("x")],lambda x:-x)
  for line in code.split("\n"):
    parseLine(line,functions)

  if args.verbose:
    for f in functions.values():
      print(f)
  f=functions.get("f")
  if f is not None:
    if len(params)<len(f.args):
      raise Exception(f"not enough arguments for function {f.name} need {len(f.args)} got {len(params)}")
    if len(params)>len(f.args): ## XXX? print to stderr
      print(f"WARNING: to many arguments for function {f.name} need {len(f.args)} got {len(params)}",file=sys.stderr)
    f_args=dict()
    for i in range(0, len(f.args)):
      f_args[f.args[i]]=params[i]
    print(valueToString(f.evaluate(f_args,dict(functions)),args.out_mode))

if __name__ == "__main__":
  main()
