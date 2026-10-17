from hypothesis import settings

# Twisted-heavy tests can be slow on a loaded machine; don't fail on timing.
settings.register_profile("default", deadline=None)
settings.load_profile("default")
