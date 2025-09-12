from odoo import models

class PageReloadBase(models.AbstractModel):
    _name = "page.reload.base"
    _inherit = ["page.reload.mixin"]
    _description = "Base with page refresh"

    # Override in concrete models; may return:
    # - None
    # - a single model name (str)
    # - an iterable of model names (list/tuple/set)
    def _target_model_on_change(self):
        return None

    def write(self, vals):
        res = super().write(vals)
        targets = self._target_model_on_change()
        # Always also include the current model if you want it refreshed too
        if targets is None:
            targets = self._name
        else:
            # Ensure current model is included if not already
            if isinstance(targets, str):
                targets = [targets, self._name] if targets != self._name else targets
            else:
                targets = list(set(list(targets) + [self._name]))
        self[:1].reload(target_model=targets)
        return res

    def create(self, vals_list):
        recs = super().create(vals_list)
        targets = recs._target_model_on_change()
        if targets is None:
            targets = recs._name
        else:
            if isinstance(targets, str):
                targets = [targets, recs._name] if targets != recs._name else targets
            else:
                targets = list(set(list(targets) + [recs._name]))
        recs[:1].reload(target_model=targets, extra={"is_create_mode": True})
        return recs

    # def unlink(self):
    #     targets = self._target_model_on_change()
    #     if targets is None:
    #         targets = self._name
    #     else:
    #         if isinstance(targets, str):
    #             targets = [targets, self._name] if targets != self._name else targets
    #         else:
    #             targets = list(set(list(targets) + [self._name]))
    #     res = super().unlink()
    #     self.reload_model(self.env, target_model=targets)
    #     return res
