import importlib

module_name = "microless_cpu_with_stock"
mod = importlib.import_module(module_name)

print(f"✅ 'scrape' in module? {'scrape' in dir(mod)}")
print(f"🔧 scrape(): {getattr(mod, 'scrape', None)}")
