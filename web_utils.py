# add parameters to URL in a stupid way
# spaces get replaced, the rest has to be fine :D
def concat_literal_params(url, params):
    first_val = True
    for key,value in params.items():
        value = value.replace(' ', '+')
        if first_val:
            first_val = False
            url += f"?{key}={value}"
        else:
            url += f"&{key}={value}"
    return url

