5 Python scripts anyone can use to boost their
productivity

xda-developers.com/python-scripts-bost-productivity

December 24, 2024

If you want to boost your productivity on your PC and you've exhausted all of the other tricks
and tools out there, have you considered using Python? It's a programming language, but
you can do a lot with it to boost your productivity in ways that you may not have necessarily
thought of. What's more, you don't need any advanced programming experience to use the
Python scripts shown below.

I've put every script listed here in a GitHub repository so that you can easily download and
use them. You'll need to install Python for them to work, and for some of them, you may need
to install additional libraries using pip.

5 Batch rename files in a folder

Simplify your organization

1/6

If you have a folder filled with files of various types and scattered names, you can rename
them all at once with Python. This script will take a prefix that it will then use to modify the
names of files in the folder.

For example, if you set a prefix of "Documents", it will collect all of the files in the folder,
renaming them "Document_0," "Document_1," etc with the correct file extensions. This can
be great for quickly organizing your folders if you need to.

4 Automatically sort your folders based on the file extension

Split your folders up

Do you have a folder filled with lots of different kinds of files? You can use a Python script to
automatically sort the contents of a folder into sub-folders that are named after the extension
so that you can then go through the contents easily.

This script will essentially move everything in your folder, so be mindful that you'll have to
manually undo everything if you run it and you aren't happy with the results. For example, if
you have a folder with files like this:

document1.txt
image1.jpg

2/6

notes.pdf
document2.txt

These will be sorted into the following folders:

/path/to/your/folder/TXT/document1.txt
/path/to/your/folder/TXT/document2.txt
/path/to/your/folder/JPG/image1.jpg
/path/to/your/folder/PDF/notes.pdf

This can make it really easy if you have a massive folder of various different files to sort
through.

Related
How to add Python to PATH in macOS

Save time by streamlining your Python development setup in macOS.

1

3 Convert your CSV files to Excel files

Excel has a few advantages

3/6

While Excel can do this natively, you can convert all of the CSV files in a folder to Excel files.
This will batch-convert them for you, so if you have a lot of CSV files, this will get them all
done at once for you.

Excel files have a number of advantages over CSV, including support for multiple sheets,
more advanced formatting, native compression, support for formulas, and much more. If you
plan to do a lot of advanced spreadsheet work, then you should be using Excel files, even
though CSV files are incredibly simplistic and universal.

2 Combine multiple PDFs into one

Make them easier to search through

4/6

Source: mockup.photos

If you have a lot of PDF files that you want to concatenate into one big file, Python makes it
really, really easy. The PyPDF2 library has a PdfMerger function that can take PDF files as
an argument and stick them all together.

This is incredibly useful for a few reasons, including if you just have a lot of very similar
documents and want to be able to search through them at the one time in one big file. Plus,
you can share one file with someone as opposed to multiple.

1 Organize your Downloads folder

Archive all the old stuff

5/6

Is your Downloads folder a complete mess? Mine certainly is, and there's a handy way to
deal with that mess with a simple script. Rather than letting things accumulate over time, this
script will check the timestamp of every file in your downloads folder, and move them into an
"Archive" sub-folder if it's older than 30 days.

Organization can be quite difficult, and the Downloads folder in particular can be very
overwhelming when it comes to figuring out where to even begin. This takes a lot of the hard
work out of it and means you can have a tidier downloads folder. You can then combine that
with the file extension sorter to break things down further if it helps, too.

6/6

