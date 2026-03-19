from django.forms.widgets import FileInput

class MultipleFileInput(FileInput):
    """
    Custom widget untuk upload multiple files
    """
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if 'multiple' not in self.attrs:
            self.attrs['multiple'] = True
    
    def value_from_datadict(self, data, files, name):
        return files.getlist(name)