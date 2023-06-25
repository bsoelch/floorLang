# floor
Is a programming language based on arithmetic expressions.

A floor program defines a function from a tuple of integers to the integers using only the arithmetic operators `+` `-` `*` `/`, integral powers (`^`) as well as `floor`-function

## Examples


Hello World (needs to be run with `-S` flag for string output)

```
f: -> 2645608968345021733469237830984
```

Compute the minimum of two numbers:

```
bool: x -> - floor( -x²/(x²+1))
if: c x y -> (bool c)*x+(1-(bool c))*y

lt: x y -> -(floor((x-y)/((x-y)²+1)))

min: x y -> if lt x y x y
f: a b -> min a b
```

Fibonacci sequence:

```
bool: x -> - floor( -x²/(x²+1))
lt: x y -> -(floor((x-y)/((x-y)²+1)))

intPair: x y -> x + 1/y
left: x -> floor x
right: x -> 1/(x-floor x)

# fib-step will be repeatedly applyed to its own return value
fib_step: xy -> intPair right xy (left xy +right xy)
fib: n -> (bool lt n 2)+ (1-(bool lt n 2))*(left fib_step^(n-1)(3/2))

f: n -> fib n
```


## Usage

run the python script from the console, with the following arguments

```
python floorLang.py -f <source-file> <flags> -- <parameters>
```

Flags:

- `-v` (verbose mode): print the parsed functions
- `-s` `-x` `-b` set input to string/hexadecimal/binary mode:
  parse parameters as Unicode strings (low bytes first)/hexadecimal numbers/binary numbers if no input mode is specified the parameters are parsed as decimal numbers
- `-S` `-X` `-B` set output to string/hexadecimal/binary mode:
  changes how the output will be printed

The parameters are passed as parameters to the function `f` in the program file

## Syntax

A floor program consists of a series of function from tuples of integers to the integers

The when executing a floor program the function `f` will be called with the arguments given to the program.

The syntax for a function definition is `name: arg1 ... argN -> expr`:

- First the name of the function followed by a `:`
- The a sequence of argument names separated by spaces terminated by a `->`
- The a arithmetic expression using integers, operators function arguments and previously defined functions

Example:

```
# Lines starting with # are comments

ceil: x -> - floor -x
add: x y -> x+y
f: (add ceil x floor x)/2
```

### Operators

The usual arithmetic rules for `+` `-` `*` `/` `^` apply,

Parenthesis are evaluated before exponentiation which is evaluated before multiplication and division which are evaluated before addition and subtraction.
Exponentiation is evaluated right to left, all other operations are evaluated left to right.

```
1+2*3^4^5-6   -> (1+(2*(3^(4^5))))-6
2/3/4   ->  (2/3)/4
# + and - can be used as unary operators
-1*3--4  -> ((-1)*3)-(-4)
# functions have precedence over operators
floor x + 1/2   -> (floor x)+(1/2)
```

All calculations are performed on rational numbers
If the right operand of `^` is not a integer it will be rounded down (towards minus infinity) to the nearest integer,
i.e `2^(1/2)  ->  2^0  ->  1`.
Division by zero will evaluate to `0`, this includes taking zero to negative powers.
The exception to this rule are `0/0` and `0^0` which will evaluate to `1`.

The `^` operator can also be used on functions, in this context it refers to repeated application of that function,
if the function has more than one argument, the remaining arguments will be passed to all calls.

As recursive definition: `f^n(a,b1,...bN) = f^(n-1)(f(a,b1,...,bN),b1,...,BN)` 

Examples:
```
inc: n -> n+1
add: a b -> inc^a b
mult: a b -> add^b 0 a
```

### Conditional Statements

The basic building block for control flow this is that `floor x` evaluates to `0` if `x` is in `(0,1)` but to `-1` if x is in `(-1,0)`.

This asymmetry can be used to construct indicator functions for different conditions for instance:

- being a positive/negative: `isPositive: x -> -floor(-x/(x^2+1))` `isNegative: x -> -floor(x/(x^2+1))`
- being nonzero: `bool: x -> - floor( -x²/(x²+1))`
- being smaller than a given number: `lt: x y -> -(floor((x-y)/((x-y)²+1)))`
- being a integer: `isInt: x -> 1+floor((floor x) - x)`

Using indicator functions is is possible to simulate conditional statements:

```
if: c x y -> (bool c)*x+(1-(bool c))*y
# if(c,x,y) evaluates to x if c is nonzero and to y is c is zero

# this can for instance be used to define minimum and maximum functions
min: x y -> if lt x y x y
max: x y -> if lt x y y x
```



