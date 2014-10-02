#!/ebio/ag-neher/share/programs/EPD/bin/python
'''
author:     Taylor Kessinger & Richard Neher
date:       10/07/2014
content:    generate beta coalescent trees and calculate their SFS
'''
import numpy as np
import random as rand
import scipy.special as sf
from Bio import Phylo
from betatree import *

def logit(x):
    return np.log(x/(1-x))

class SFS(betatree):
    '''
    class the generates many trees and accumulates an SFS.
    trees are generated by the inherited betatree class
    '''
    def __init__(self, sample_size, alpha=2):
        betatree.__init__(self,sample_size, alpha)
        self.alleles=[]
        self.sfs=None

    def glob_trees(self, ntrees=10):
        '''
        generate many trees, accumulate the SFS
        parameters:
        ntrees -- number of trees to generate
        '''
        for ti in xrange(ntrees):
            self.coalesce()
            self.alleles.append([(clade.weight,clade.branch_length) 
                                 for clade in self.BioTree.get_terminals()
                                 +self.BioTree.get_nonterminals()])

    def getSFS(self, ntrees = 10):
        '''
        calculate an SFS based on ntrees trees
        ntrees -- number of trees used to calculate the average SFS
        '''
        self.glob_trees(ntrees)
        self.sfs = np.zeros(self.n+1)
        # loop over all "alleles". an allele here is a branch of the tree
        # with length l and w descendants. 
        for aset in self.alleles:
            for w,l in aset:
                self.sfs[w]+=l
        self.sfs/=ntrees


    def binSFS(self, mode = 'logit', bins=10):
        '''
        use the precalcutated SFS and bin it.
        mode -- one of linear, log, or logit. a binning with bins bins will be generated
        bins -- a user-specified binning if bins is iterable, otherwise the number of bins
        '''
        if np.iterable(bins):
            nbins = np.array(bins)
        else:
            if mode=='logit':
                nbins = np.exp(0.9*np.log(self.n)*np.linspace(-1,1,bins+1))
                nbins = nbins/(1.0+nbins)
                self.bin_center = np.sqrt(nbins[1:]*nbins[:-1])
            if mode=='linear':
                nbins=np.linspace(0,1,bins+1)
                self.bin_center = 0.5*(nbins[1:]+nbins[:-1])
            if mode=='log':
                nbins = np.exp(0.9*np.log(self.n)*np.linspace(-1,1,bins+1))
                self.bin_center = np.sqrt(nbins[1:]*nbins[:-1])

        self.bin_width = nbins[1:]-nbins[:-1]

        self.binned_sfs, tmp = np.histogram(np.linspace(0,1,self.n+1), 
                                            weights = self.sfs/self.n, bins = nbins)
        self.binned_sfs/=self.bin_width


    def saveSFS(self,fname):
        '''
        writes and existing sfs to the file fname. if fname ends on gz, the file 
        will be gzipped. if no sfs has been calculated, it will call getSFS()
        '''
        if self.sfs is None:
            self.getSFS()        
        np.savetxt(fname, self.sfs)


    def loadSFS(self,fname, alpha=None):
        '''
        load a previously saved SFS from file. checks for one-d vector, uses length of the 
        vector as SFS as sample size
        '''
        tmp  = np.loadtxt(fname)
        if len(tmp.shape)==1:
            self.n = tmp.shape[0]-1
            self.sfs = tmp
            self.alpha=alpha
        else:
            self.sfs=None
            print "expect a one dimensional vector, got object with shape",tmp.shape

if __name__=='__main__':
    import matplotlib.pyplot as plt
    plt.ion()
    file_ending = '.dat.gz'
    calc=False
    for alpha in [2,1.5, 1]:
        n=1000
        mySFS = SFS(n,alpha=alpha)
        if calc:
            print "calculating spectra for alpha =",alpha
            mySFS.getSFS(ntrees=1000)
            mySFS.saveSFS('examples/sfs_'+'_'.join(map(str, ['alpha', alpha, 'n', n]))
                          +file_ending)
        else:
            print "loading spectra for alpha =",alpha
            mySFS.loadSFS('examples/sfs_'+'_'.join(map(str, ['alpha', alpha, 'n', n]))
                          +file_ending)

        plt.figure('regular')
        mySFS.binSFS(mode='logit', bins=20)
        plt.plot(mySFS.bin_center, mySFS.binned_sfs, label=r'$\alpha='+str(alpha)+'$')

        plt.figure('logit')
        mySFS.binSFS(mode='logit', bins=20)
        plt.plot(logit(mySFS.bin_center), mySFS.binned_sfs, label=r'$\alpha='+str(alpha)+'$')

        plt.figure('log')
        mySFS.binSFS(mode='log', bins=20)
        plt.plot(mySFS.bin_center, mySFS.binned_sfs, label=r'$\alpha='+str(alpha)+'$')
        

    plt.figure('regular')
    plt.yscale('log')
    plt.xlim(0,1)
    plt.legend(loc=9)
    plt.xlabel('derived allele frequency')
    plt.xlabel('site frequency spectrum')

    plt.figure('logit')
    plt.yscale('log')
    plt.xlim(-np.log(n),np.log(n))
    tick_locs = np.array([0.001, 0.01, 0.1, 0.5, 0.9, 0.99, 0.999])
    plt.xticks(logit(tick_locs), map(str,tick_locs))
    plt.legend(loc=9)
    plt.xlabel('derived allele frequency')
    plt.xlabel('site frequency spectrum')


    plt.figure('log')
    plt.yscale('log')
    plt.xscale('log')
    plt.xlim(1.0/mySFS.n,1)
    plt.legend(loc=9)

    plt.xlabel('derived allele frequency')
    plt.xlabel('site frequency spectrum')
