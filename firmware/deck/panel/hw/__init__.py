"""Thin drivers for the real panel's chips, written against the datasheets
(DECISIONS.md #68 for the PCA9685's output mode). Each takes its bus or
device as an argument, so tests drive them with fakes and nothing here
imports a board library at module level."""
