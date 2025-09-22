from odoo import models

def _to_iterable_models(target_model, default_name):
    """
    Normalize target_model to a list of model names.
    - None -> [default_name]
    - str  -> [str]
    - iterable of str -> list(str)
    """
    if target_model is None:
        return [default_name]
    if isinstance(target_model, str):
        return [target_model]
    # Assume iterable of strings
    return [m for m in target_model if m]

class PageReloadMixin(models.AbstractModel):
    _name = "page.reload.mixin"
    _description = "Broadcast page refresh over bus"

    def reload(self, target_model=None, extra=None):
        models_to_broadcast = _to_iterable_models(target_model, self._name)
        token = self.env.context.get("editor_token")
        for model_name in models_to_broadcast:
            payload = {"model_name": model_name}
            if token:
                payload["editor_token"] = token
            if extra:
                payload.update(extra)
            self.env["bus.bus"].sudo()._sendone("broadcast", "page_refresh", payload)

    # @classmethod
    # def reload_model(cls, env, target_model=None, extra=None):
    #     models_to_broadcast = _to_iterable_models(target_model, cls._name)
    #     token = env.context.get("editor_token")
    #     for model_name in models_to_broadcast:
    #         payload = {"model_name": model_name}
    #         if token:
    #             payload["editor_token"] = token
    #         if extra:
    #             payload.update(extra)
    #         env["bus.bus"].sudo()._sendone("broadcast", "page_refresh", payload)




