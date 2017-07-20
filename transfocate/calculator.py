


import itertools




class Calculator(object):
    """Class for the transfocator beryllium lens calculator.

    Attributes
    ----------
    xrt_lenses : list
        A list of the xrt prefocus lenses
    tfs_lenses : list
        A list of the beryllium transfocator lenses
    xrt_limit : float 
        The hard limit i.e. minimum effective radius that the xrt lens array can safely
        have
    tfs : float
        The hard limit i.e. maximum effective radius that tfs lense array can
        safely have
    """

    def __init__(self, xrt_lenses, tfs_lenses, xrt_limit=None, tfs_limit=None):
        self.xrt_lenses=xrt_lenses
        self.tfs_lenses=tfs_lenses

    @property
    def combinations(self):
        """Method calculates and returns all possible combinations of the xrt
        and tfs lense arrays

        Returns
        -------
        list
            Returns a list of all possible combinations of the xrt and tfs
            lense arrays
        """
        
        all_combo=[]
        prefocus_combo=self.xrt_lenses
        tfs_combo=[]
        self.tfs_lenses.append(None)
        self.xrt_lenses.append(None)
        for i in range(len(self.tfs_lenses)+1):
            z=list(itertools.combinations(self.tfs_lenses,i))
            for index in range(len(z)):
                tfs_combo.append(z[index])
            print (len(tfs_combo))
            #print (tfs_combo)
        for prefocus in prefocus_combo:
            for combo in tfs_combo:
                all_combo.append([prefocus,combo])
        #print (len(all_combo))
        return all_combo
