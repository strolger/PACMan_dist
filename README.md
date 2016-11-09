Welcome to PACMan, the Proposal And Committee Manager. 

Instructions:
1. Use pip to install the following packages:
	Reverend
	stemming
	urllib
	urllib2
	xml


3. Run PACManSort.py by choosing to test or train on one of three types
of corpus-HST proposals, other types of text, or author. Commands for
these and additional options are below.

Syntax : PACManSort.py [options] corpus.txt

Options:
 --help, -h       : print this help
 --verbose, -v    : verbose mode
 --bayes X        : defines a different Bayes file
 --train          : switch from test/application mode to training mode
 --authors        : assumes corpus.txt is a list of authors for ADS Crawl
                    default is corpus is text, like science justification
 --exact_names    : if authors specified, uses exact name match in ADS Crawl
 --first_author   : if authors specified, uses only first author results from ADS Crawl
 --nyears X       : specify the number of years past in the abstract
 bibliography of ADS Crawl
 --plot           : plot testing results (if aplicable)
 --hst            : preset for HST proposals


4. [Unfinished] Results will be returned to a file called
proposal_results_date.txt. Translate category acronyms using the
included Cy24Acronyms_translate.txt as a guide.


* Note: Inputs should be in the form of .txtx files. PDFs can be
  converted using: ps2ascii input.pdf [ output.txtx ]


How PACMan works:


Naive Bayesian classification is a popular and effective method for
differentiating between types of documents. In contrast to a simple
frequentist classification, Bayesian classification takes into account
posterior probability, determined by training on pre-classified data-in
this case, Hubble science proposals. During training, each proposal of
known science category is broken down into a 'bag' of its component
words. As these lists of science words are parsed, the classifier builds
a probabilistic model for each word using Bayes' Theorem.



Fisher's Method

Once the Bayesian classifier is trained, it is ready to parse new,
unclassified proposals. The data for each word found in a proposal are
combined using Fisher's Method to form an overall probability that the
proposal falls into an established category. The formula combines
p-values from a number of independent tests into one overall p-value
with chi-squared distribution. The results are normalized, yielding a
percent likelihood that the proposal belongs in each category.



Improvements

Several measures can be taken in order to make the spam classifier even
more accurate. Words like "a", "the", and "it", which are clearly
unrelated to science categories, are removed before
classification. Conversely, words that are almost always found in only
one science category-"planet" in "Planets", for example-can be used to
prime PACMan before training.
