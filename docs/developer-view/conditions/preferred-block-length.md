--8<--
user-view/list-of-conditions.md:preferred-block-length
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/rotate_shifts_forward.py"
for length, var in [(len, cast(IntVar, var)) for (len, var) in block_length_vars]:
    k: int = abs(length - self._target_block_length)
    penalties.append(k * var)
penalties.append(
    abs((self._max_block_length + 1) - self._target_block_length) * unmatched_block,
)
```
