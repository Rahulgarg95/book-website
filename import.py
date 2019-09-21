import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))
d = db()

#d.execute("INSERT INTO books (isbn, title, author, year) VALUES('1B','fedfkln','erweerwe',1995)")

f=open("books.csv")
reader=csv.reader(f)
for isbn, title, author, year in reader:
    print("Isbn: " + isbn + " title: " + title + " author: " + author + " year: " + str(year))
    '''str1='"' + str(isbn) + '"' + ','+ '"' + str(title) + '"' + ',' + '"' + str(author) + '"' + ',' + '"' + str(year) + '"'
    print(str1)
    cmd="INSERT INTO books (isbn, title, author, year) VALUES(" + str1 + ")"
    print("CMD:     " + cmd)
    cmd1='"'+cmd+'"' '''
    d.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
    #d.execute(cmd)    
d.commit()