from bluesky import plans
from bluesky import plan_stubs
from types import SimpleNamespace

# Note that the dict has the structure {[alias1, alias2, ...]:plan_stub, ...}
_plan_stubs_to_alias = {('move', 'mv'): plan_stubs.mv,
                        ('relative_move', 'mvr'): plan_stubs.mvr}

# Note that the dict has the structure {[alias1, alias2, ...]:'plan', ...}
# noinspection PyRedundantParentheses
_plans_to_alias = {('count',): plans.count,
                   ('scan',): plans.scan,
                   ('relative_scan', 'rel_scan'): plans.rel_scan,
                   ('grid_scan',): plans.grid_scan,
                   ('relative_grid_scan',
                    'rel_grid_scan'): plans.rel_grid_scan,
                   ('list_scan',): plans.list_scan,
                   ('relative_list_scan',
                    'rel_list_scan'): plans.relative_list_scan,
                   ('list_grid_scan',): plans.list_grid_scan,
                   ('relative_list_grid_scan',
                    'rel_list_grid_scan'): plans.rel_list_grid_scan,
                   ('log_scan',): plans.log_scan,
                   ('relative_log_scan',
                    'rel_log_scan'): plans.relative_log_scan,
                   ('spiral',): plans.spiral,
                   ('relative_spiral', 'rel_spiral'): plans.relative_spiral,
                   ('spiral_fermat',): plans.spiral_fermat,
                   ('relative_spiral_fermat',
                    'rel_spiral_fermat'): plans.rel_spiral_fermat,
                   ('spiral_square',): plans.spiral_square,
                   ('relative_spiral_square',
                    'rel_spiral_square'): plans.rel_spiral_square}


class PlanCollectorSub(SimpleNamespace):
    """
    A class used to initialize child attributes with methods for PlanCollector's

    This class is to be used with the `PlanCollector` class when you want to add
    an extra level of plans that contain no child collections, only child plans.

    Parameters
    ----------
    plans for methods : {str: func}
        A dictionary mapping method tuples of method names to methods for the
        sub class.
    name : str
        The name of the sub-class, usually matches this instances attribute name
    parent : PlanCollector
        The plan collector object that is this instances parent.

    Attributes
    ----------
    name : str
        The name of this instance
    parent : PlanCollector
        The plan collector object that is this instances parent.

    Methods
    _______
    __str__() :
        Returns a user friendly formatted string showing the structure of the
        instance including all of the methods from methods_to_import but not
        the 'name' or 'parent' attributes.
    __dir__() :
        Returns a list of attribute name strings to be used to define what
        options are available when doing tab-to-complete.
    """
    def __init__(self, plans_for_methods, name, parent):
        super().__init__(**plans_for_methods)

        self.name = f'{parent.name}_{name}'
        self.parent = parent

    def __str__(self):
        """
        A custom __str__ method that prints a formatted list of plans.

        This method is designed to print a formatted list of plans associated  with
        this sub-class that has no lower subclasses.

        Returns
        -------
        output: str
            A formatted string that should be printed when using print(self)
        """
        output = f'\n{self.name}:'
        for name, plan in self.__dict__.items():
            if name not in ['name', 'parent']:
                description = plan.__doc__.split('\n')[0].strip() \
                    if plan.__doc__.split('\n')[0] else (
                    plan.__doc__.split('\n')[1].strip())

                output += f'\n    {name}:    {description}'

        return output

    def __dir__(self):
        """
        Used to limit the number of options when using tab to complete.

        This method is used to give the list of options when using pythons tab
        to complete process. It gives all of the method attributes but not the
        'name' and 'parent' attributes.

        Returns
        -------
        attribute_list : list[str]
            A list of attribute names to be included when using tab-to-complete
        """
        attribute_list = [plan for plan in self.__dict__.keys()
                          if plan not in ['name', 'parent']]

        return attribute_list


class PlanCollector(SimpleNamespace):
    """A class used to collect together the plans to be used at ARI and SXN,

    This is a 'collector' class that is designed to hold together the plans that
    are used at both ARI and SXN. It will include all of the builtin
    `bluesky.plans` (but only one alias of each) as well as the builtin
    `bluesky.plan_stubs` mv (as `plan.move`) and mvr (as `plan.relative.move`).
    Note that 'relative' plans that move relative to the current location will
    be grouped in a child `self.relative` object.

    Additional, ARI & SXN specific, plans can/will also be added (see attribute
    list below).

    Parameters
    ----------
    plans for methods : {str: func}
        A dictionary mapping method tuples of method names to methods for the
        sub class.
    name : str
        The name of the object, usually matches this instances attribute name

    Methods
    _______
    __str__() :
        Returns a user friendly formatted string showing the structure of the
        instance including all of the methods from plans_to_import,
        plan_stubs_to_import and any PlanCollectorSub attributes but not the
        'name' attribute.
    __dir__() :
        Returns a list of attribute name strings to be used to define what
        options are available when doing tab-to-complete.

    """
    def __init__(self, plans_for_methods={}, name=None):

        if name:
            self.name = name
        else:
            self.name = 'PlanCollector'

        super().__init__(**{k[0]: v for k, v in plans_for_methods.items()
                            if not k[0].startswith('rel')})
        self.relative = PlanCollectorSub(plans_for_methods={
            k[0]: v for k, v in plans_for_methods.items()
            if k[0].startswith('rel')},
            name='relative', parent=self)

    def __str__(self):
        """
        A custom __str__ method that prints a formatted list of plans.

        This method is designed to print a formatted list of plans and any
        sub-classes that have plans.

        Returns
        -------
        output: str
            A formatted string that should be printed when using print(self)
        """
        output = f'\n{self.name}:'
        for name, plan in self.__dict__.items():
            if name not in ['name', 'parent']:
                if plan.__dict__:  # if plan has attributes
                    output += f'\n    {plan.__str__().replace(
                        '\n', '\n    ').replace(
                        f'{self.name}_', '')}'
                else:
                    description = plan.__doc__.split('\n')[0].strip() \
                        if plan.__doc__.split('\n')[0] else (
                        plan.__doc__.split('\n')[1].strip())

                    output += f'\n    {name}:    {description}'

        return output

    def __dir__(self):
        """
        Used to limit the number of options when using tab to complete.

        This method is used to give the list of options when using pythons tab
        to complete process. It gives all of the method attributes and any
        PlanCollectorSub attributes but not the 'name' attribute.

        Returns
        -------
        attribute_list : list[str]
            A list of attribute names to be included when using tab-to-complete
        """
        attribute_list = [plan for plan in self.__dict__.keys()
                          if plan not in ['name']]

        return attribute_list
