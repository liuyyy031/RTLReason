# Combinational Cache Tag Lookup

Design a synthesizable combinational module `cache_tag_lookup`. Compare one
lookup tag against a parameterized set of valid ways. Return the lowest-numbered
matching way and its data. Invalid ways never hit; a miss returns zero-valued
way and data. Use the exact packed-bus layout and semantics in
`interface_semantics.json`.
