#!/usr/bin/env python
'''
Routine to categorize proposals or panelists for the ST-TAC

Syntax : PACMan.py [options] corpus.txt

Options:
 --help, -h       : print this help
 --verbose, -v    : verbose mode
 --train          : switch from test/application mode to training mode
 --bayes X        : defines a different Bayes file 
 --authors        : assumes corpus.txt is a list of authors for ADS Crawl
                    default assumes corpus is text, like science justification
 --exact_names    : if authors specified, uses exact name match in ADS Crawl
 --first_author   : if authors specified, uses only first author results from ADS Crawl
 --nyears X       : specify the number of years past in the abstract bibliography of ADS Crawl
 --plot           : plot testing results (if aplicable)
 --hst            : preset for HST proposals (no corpus.txt file necessary)

This script parses proposals of unknown categorization, assigning
probabilities that each falls in any given category.  Before running,
create a category_aliases.txt file which describes the categories, and
any other alias Before running this program in HST mode, translate
proposals into file format .txtx (PDFs can be translated using ps2ascii
command)

If run in test/analysis mode (without train option), will require a
PACManData.bay file. A sample one is provided in the lib directory,
which is chosen by default unless otherwise specified.

Two input file are required:
- corpus.txt: document to be catagorized, or (in training mode) trained from. Input on command line.
- category_synonyms.txt: defines the categories for identification. Must be consistent with the Bayes file definitions.

Non-normalized results containing three most likely categories are returned to the command line.
Additional details are provided in the README.txt file.

L. Strolger and S. Porter 11/2016
'''

import os,sys,pdb,scipy,glob,pickle
from pylab import rec, where, array
import string
import re
import getopt
from reverend.thomas import Bayes
from stemming.porter2 import stem
software = os.path.dirname(os.path.realpath(__file__))
sys.path.append(software)



def main():

     verbose = False
     train = False # assumes in a testing/application mode--- this switches to training
     authors = False # assumes evaluating text--- this switches to author ADS abstracts
     exact_names = False
     first_only = False
     nyears = 10
     plotit = False
     hst = False
     clobber = False
     rs_exceptions = ''

     hkap_file = os.path.join(software,'libs/PACManData.bay')

     

     try:
          opt,arg = getopt.getopt(
               sys.argv[1:],'v,h',
               longopts=['verbose','bayes=','train','authors',
                         'exact_names','first_only',
                         'exceptions=',
                         'nyears=','plot','hst','clobber'])
     
     except getopt.GetoptError:
          print 'Error : incorrect option or missing argument.'
          print __doc__
          sys.exit(1)
     for o, a in opt:
          if o in ['-h','--help']:
               print __doc__
               return(0)
          elif o in ['-v','--verbose']:
               verbose = True
          elif o == '--bayes':
               hkap_file = a
          elif o == '--train':
               train = True
          elif o == '--authors':
               authors = True
          elif o == '--exact_names':
               exact_names = True
          elif o == '--first_only':
               first_only = True
          elif o == '--nyears':
               nyears = int(a)
          elif o == '--plot':
               plotit = True
          elif o == '--hst':
               hst = True
          elif o == '--clobber':
               clobber = True
          elif o == '--exceptions':
               rs_exceptions = a
               
     if not hst and len(arg) !=1 :
          print __doc__
          print "\n Too many or too few inputs. You must specify the input corpus text file\n"
          print (arg)
          sys.exit(1)
     
     if hst:
          corpus = os.path.join(software,'libs/proposal.txtx')
     else:
          corpus = arg[0]

     results,categories=run(corpus, verbose=verbose, hkap_file=hkap_file, train=train, authors=authors, exact_names=exact_names, first_only=first_only, nyears=nyears, plotit=plotit, hst=hst, clobber=clobber, rs_exceptions=rs_exceptions)
     return(results,categories)
          
def run(corpus, verbose=False, hkap_file=os.path.join(software,'libs/PACManData.bay'), train=False, authors=False, exact_names=False, first_only=False, nyears=10, plotit=False, hst=False, clobber=False, rs_exceptions=''):
     f = open(os.path.join(software,'category_synonyms.txt'),'r')
     lines = f.readlines()
     f.close()
     acronyms = {}
     for line in lines:
          if line.startswith('#'): continue
          key, value = line.split('=')
          acronyms[key.strip()]=value.strip().split(',')
     uber_categories = acronyms

     stopwords = load_stopwords()

     dguesser = Bayes()
     dguesser.load(hkap_file)

     if not authors:
          if hst:
               ## Below, proposals are retrieved, then parsed.
               abs = parse_abstracts_proposals(corpus)    
               text = parse_science_justification_proposals(corpus) 
               justification = abs+text   
               bayesString = " "+justification
          else:
               f = open(corpus)
               lines = f.readlines()
               f.close()
               text = ''
               for line in lines:
                    if line.startswith('#'): continue
                    if not line.strip(): continue
                    text += line.strip() + ' '
               bayesString = text
          bayesString = work_string(bayesString,stopwords)
          result = dguesser.guess(bayesString)
          result = normalize_result(result)
          
     else:
          ## assumes input is a person report
          ## if .pkl report not available, creates new one
          import util
          
          records = []
          results_dict={}
          results_pkl = corpus.replace(corpus.split('.')[-1],'pkl')
          if not os.path.isfile(results_pkl) or clobber:
               f = open(corpus)
               lines = f.readlines()
               f.close()
               for line in lines:
                    if line.startswith('#'): continue
                    if not line.strip(): continue
                    info = line.rstrip().split("\t")
                    if info[0]=='': continue
                    # records.append(info[0].replace(' ','').replace('"','').replace("'",'').lower())
                    records.append(info[0].replace('"','').replace("'",'').lower())
               author_dict, cite_dict = util.adscrawl.run_authors(records, nyears=nyears, rs_exceptions=rs_exceptions)
               ## author_dict, cite_dict = util.adscrawl.run_exact_authors(records, nyears=nyears)
               pickle.dump(author_dict, open(results_pkl,'wb'))
               pickle.dump(cite_dict, open('cites.pkl','wb'))
          else:
               author_dict = pickle.load(open(results_pkl,'rb'))
               cite_dict = pickle.load(open('cites.pkl','rb'))
          for author in author_dict.keys():
               bayesString = ''
               for abstract in author_dict[author]:
                    bayesString = ' '+abstract
                    
               bayesString=work_string(bayesString,stopwords)
               result = dguesser.guess(bayesString)
               ## result = normalize_result(result)
               results_dict[author]={}
               results_dict[author]['hkap']=rec.fromrecords(result)
               try:
                    results_dict[author]['cites']=sorted(cite_dict[author],reverse=True)
               except:
                    results_dict[author]['cites']=[0]
          result = results_dict
     return(result,uber_categories)

    

def stemWords(instr):
    thisList = instr.split()
    outstr = ''
    for word in thisList:
        word = stem(word)
        outstr += ' ' + word
    return outstr

def load_stopwords():
    stopwords = open(os.path.join(software,'libs/stopwords.txt'),'r').read().split()
    stopwords += ['understand','trend','measure','sample','use','test','perform','format']
    stopwords += ['abstract','scientific','justification','proposal','figure','program']
    stopwords += ['observe', 'image', 'data','model','time','orbit','source','target']
    stopwords += ['apj','hst','nasa','aj','mnras']
    return stopwords

add_stops = ['imag','observ','use','measur','format','studi','coi','sourc','target']
add_stops += ['propos','orbit','target','result','object','provid']
add_stops += ['fig']

def filterStopwords(instr, stopwords):
    # instr is a text string containing stopwords
    # stop words is a list of strings to remove from instr
    textwords = instr.split()
    markedtext = []
    for t in textwords:
        if t.lower() in stopwords:
            continue
        else:
            markedtext.append(t.lower())
    ## uncomment to remove repeated elements
    # markedtext = list(set(markedtext)) # actually, don't!
    markedtext.sort()
    outstr = string.join(markedtext, ' ')

    return outstr

def parse_old_abstracts(file):
    f = open(file,'r')
    lines = f.readlines()
    f.close()
    text_dict={}
    for line in lines:
        if not line.strip(): continue
        if (('HST Cycle' in line)&('proposal' in line)&(len(line.split(':')[0])==27)):
            try:
                nkey = int(line.split('proposal')[1].split()[0][:-1])
            except:
                pdb.set_trace()
        else:
            text_dict[nkey]=line.strip()
    return(text_dict)

def parse_abstracts_proposals(file):
    f = open(file,'r')
    lines = f.readlines()
    f.close()
    record = False
    text = '' 
    for line in lines:
        if not line.strip(): continue
        if (line.strip().lower()=='abstract'):
            record = True 
        if (('principal' in line.lower())&('investigator' in line.lower())):
            record = False
        if record:
            text += line.strip()+' '
    return(text)

def parse_science_justification_proposals(file):
    f = open(file,'r')
    lines = f.readlines()
    f.close()
    record = False
    text = '' 
    for line in lines:
        if not line.strip(): continue
        if (('scientific' in line.lower())&('justification' in line.lower())):
            record = True 
        if (('description' in line.lower())&('observations' in line.lower())):
            record = False
        if record:
            text += line.strip()+' '
    return(text)


def parse_keywords_proposals(file):
    f = open(file,'r')
    lines = f.readlines()
    f.close()
    kwds = []
    for line in lines:
        if line.lower().startswith('scientific keywords'):
            kwds+=line.lower().replace('scientific keywords: ','').rstrip().split(',')
    return(kwds)

def parse_category_proposals(file):
    f = open(file,'r')
    lines = f.readlines()
    f.close()
    cats = []
    for line in lines:
        if line.lower().startswith('scientific category'):
            cats+=line.lower().replace('scientific category: ','').rstrip().split(',')
    return(cats)


def cleanup_abstracts(abstracts):
    out = {}
    for k,v in abstracts.items():
        if len(v.split()) > 50:
            out[k]=v
    return(out)
    
def normalize_result(result):
    out=[]
    tot = 0
    for item in result:
        tot += item[1]
    for item in result:
        out.append((item[0],item[1]/tot))
    return(out)

def return_most_probable(result, categories):
     out=[]
     tprob = 0
     cnt = 0
     while tprob < 0.60 and cnt <=len(categories.keys())-2:
          try:
               tprob += float(result[cnt][1])
          except:
               pdb.set_trace()
          cnt+=1
     return(result[:cnt])


# need this to strip punctuation
replaceThesePunctuation = string.punctuation
#replaceThesePunctuation = re.sub('-','',replaceThesePunctuation)
#replaceThesePunctuation = re.sub('/',' ',replaceThesePunctuation)
nopunk = re.compile('[%s]' % re.escape(replaceThesePunctuation))


def work_string(String,stopwords):

     # strip punctuation
     String = nopunk.sub('',String)
     # strip numbers
     String = re.sub('\\b[0-9]+\\b','',String)        
     # remove annoying characters
     String = re.sub(r'[\xc2\xe2\xbc\xbd\xef\xb2]','',String)
     # lose dangling dashes
     #String = re.sub('\\b\\w+-\\b','',String)
     #String = re.sub('\\b-\\w+\\b','',String)
     String = filterStopwords(String, stopwords)
     
     # lose single character words
     List = String.split()
     outstring = ''
     for item in List:
          if len(item) > 1:
               outstring += ' ' + item
     String = outstring
     # now, stem words
     String = stemWords(String)
     # filter common stems
     String = filterStopwords(String, add_stops)

     return(String)



def hindex(list):
     for i,item in enumerate(sorted(list,reverse=True)):
          if i > item: break
     return(i+1)




if __name__=='__main__':
     (results,categories)=main()
     #results=return_most_probable(results,categories)
     pickle.dump(results,open('ers_results.pkl','wb'))

     ## output='output.txt'
     ## if os.path.isfile(output): os.remove(output)
     ## f=open(output,'w')
     ## for author in results.keys():
     ##      print '%-30s\t' %(author),
     ##      f.write('%-30s\t' %(author)),
     ##      for field in results[author]['hkap']['f0']:
     ##           category = where(array(results[author]['hkap']['f0'] == field))
     ##           score = array(results[author]['hkap']['f1'])[category]
     ##           print '%s=%0.2f\t' %(field, score),
     ##           f.write('%s=%0.2f\t' %(field, score)),
     ##      abs = sorted(list(set(results[author]['cites'])))
     ##      nabs = len(abs)
     ##      hind = hindex(abs)
     ##      print '%02d\t%02d' %(nabs,hind)
     ##      f.write ('%02d\t%02d\n' %(nabs,hind))
     ## f.close()
     
     
     
    
