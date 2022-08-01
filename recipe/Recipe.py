from collections import defaultdict
import numpy as np
import pandas as pd

class Recipe:
    """A class to process hierarchical formulation data
    """

    def __init__(self, df: pd.DataFrame, params: dict = None, exclude_highest_level = "auto", name: str = None):
        
        self.df_ = df
        self.df_.columns = [x.strip() for x in self.df_.columns]
        
        if params is None:
            self.params = {"ing": "Component", "qty": "Qty", "lvl": "Level"}
        else:
            self.params = params

        self.ing_key, self.qty_key, self.lvl_key = list(self.params.keys())[:3]
        self.ing_col, self.qty_col, self.lvl_col = list(self.params.values())[:3]
        
        if exclude_highest_level == "auto":
            pass
            
        self.highest_level = self.df_[self.lvl_col].min()
        self.recipe_ = self.df_[self.df_[self.lvl_col] > 1].reset_index(drop=True)
       
        if name is None:
            self.name = df.loc[df[self.lvl_col] == self.highest_level, self.ing_col][0]
        else:
            self.name = name
        
        self.rec_dict = defaultdict(self.dict_template)
   
    def dict_template(self):
       return {key: [] for key in self.params.keys()}
   
    def copy_to_dict(self, idx, level):
        for key, colname in self.params.items():
            self.rec_dict[level][key].append(self.recipe_.loc[idx][colname])
    
    def __repr__(self):
        return f"Recipe(df)"
    
    def __str__(self):
        n_components = self.recipe_.shape[0]
        return "{} recipe with {} components".format(self.name, n_components)
    
    def traverse_recipe(self, idx = 0, start_level = 1, max_level = np.inf):

        current_level = self.recipe_.loc[idx, self.lvl_col]
            
        if (idx == self.recipe_.index.max()):
            previous_level = self.recipe_.loc[idx-1, self.lvl_col]
            
            if (current_level <= max_level) and (previous_level >= current_level):
                self.copy_to_dict(idx, level = max_level)
                return None # default_dict
            
            elif (idx == self.recipe_.index.max()) and (current_level > max_level):
                return None # default_dict
            
        else:
            next_level = self.recipe_.loc[(idx+1), self.lvl_col]
            
            if ~(next_level <= current_level) and ~(current_level > max_level) and (next_level > max_level):
                self.copy_to_dict(idx, level = max_level)
                self.traverse_recipe(idx + 1, start_level, max_level)
                
            elif (next_level <= current_level) and ~(current_level > max_level) and ~(next_level > max_level):
                self.copy_to_dict(idx, level = max_level)
                self.traverse_recipe(idx + 1, start_level, max_level)
                
            else:
                self.traverse_recipe(idx + 1, start_level, max_level)

    def extract_recipe(self, max_level = np.inf, aggregate = False, aggregate_by = None, sort = True, sort_by = None, ascending = False):

        if max_level in self.rec_dict.keys():
            res = pd.DataFrame(self.rec_dict[max_level])
        else:
            self.traverse_recipe(idx = 0, max_level = max_level)
            res = pd.DataFrame(self.rec_dict[max_level])
            
        if aggregate:
            if aggregate_by is None:
                aggregate_by = self.ing_key

            res = res.groupby(aggregate_by).sum().reset_index()[[self.ing_key, self.qty_key]]
            if sort:
                if sort_by is None:
                    sort_by = self.qty_key
        
                res = res.sort_values(sort_by, ascending = ascending).reset_index(drop=True)

        return res
    
    @property
    def df(self):
        return self.df_
    
    @property
    def recipe(self):
        return self.recipe_
    
    @classmethod
    def from_csv(cls, filepath: str, *args, **kwargs):
        df = pd.read_csv(filepath, *args, **kwargs)
        return cls(df)

    @classmethod
    def from_excel(cls, filepath: str, *args, **kwargs):
        df = pd.read_excel(filepath, *args, **kwargs)
        return cls(df)