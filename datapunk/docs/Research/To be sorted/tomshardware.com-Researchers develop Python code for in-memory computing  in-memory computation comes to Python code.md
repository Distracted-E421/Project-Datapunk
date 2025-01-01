Researchers develop Python code for in-memory
computing — in-memory computation comes to Python
code

tomshardware.com/pc-components/cpus/researchers-develop-python-code-that-is-compatible-with-in-memory-

computing-python-commands-converted-into-machine-code-to-be-executed-in-the-computers-memory

Aaron Klotz

November 12, 2024

(Image credit: TSMC and ITRI)
In-memory computing has been in development for a while; however, software has yet to be
released or compatible with this computing architecture. Techxplore reports that Technion
researchers have developed software that works with processing in memory designs,
specifically with Python code.

The researchers purportedly developed a theory for building a programming language with
in-memory computing in mind. The software they created converts Python commands into
machine code executed directly in the computer's memory.

This new computer language is dubbed PyPIM (Python Processing-in-Memory). Just like API
conversion layers such as DXVK (DirectX to Vulkan), PyPIM is a conversion layer that
converts conventional Python code into code that can run on this new type of computing
method. As a result, Python programmers can write the same way they write for conventional
computers and don't need to adapt their writing style for in-memory computing.

1/2

Techxplore reveals that software is one of the crucial aspects of in-memory computer
processing that has remained utterly unexplored until now. Compute code written for
conventional computers has purportedly "barely changed" since the 1940s. Professor
Shahar Kvatinsky from the Andrew and Erna Viterbi Faculty of Electrical and Computer
Engineering reveals that writing code for in-memory computing is so radically different from
conventional computing that "...some of the existing building blocks of computer science
unusable..."

Without a conversion layer such as PyPIM, developing applications compatible with
processor-in-memory support would have been very difficult. The low-level machine code
would need to be rewritten to accommodate processing some calculations in memory and
the rest on the CPU.

In-memory computing is a new way of computing that aims to solve the memory latency
problem. As the name suggests, in-memory computing enables the system memory to do
some calculations the CPU would do otherwise, cutting down the amount of data that must
be transferred between the CPU and DRAM.

Samsung and TSMC are actively working on memory capable of doing this, featuring MRAM
memory cells. In-memory computing is still in the prototype phase, but progress is being
made on the hardware side to make it a viable technology. With the help of conversion layers
like PyPIM, software should be developed to support this computing method.

Aaron Klotz

Contributing Writer

2/2

