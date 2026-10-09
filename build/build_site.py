"""Rebuild index.html: python generate_data.py && node geo.mjs && python build_site.py"""
t = open("template.html").read()
open("../index.html", "w").write(t.replace("__DATA__", open("data.json").read()).replace("__GEO__", open("geo.json").read()))
print("index.html rebuilt")
