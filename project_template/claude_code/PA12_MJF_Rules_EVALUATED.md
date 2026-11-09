# MANUFACTURING RULES — <PROCESS AND MATERIAL> (evaluated for this project)

*The kit pushes this file into every session under this exact name, whatever the process is: it is the constraint on
every edit that no geometry gate can check. Replace the placeholders with the limits of the process this part is made
by, taken from the maker's design guide and stated as numbers. Say where each number comes from. Delete a row that does
not apply; never leave a placeholder where a number should be.*

| rule | limit | source |
|---|---|---|
| minimum wall thickness | <mm> | <design guide, section> |
| minimum hole diameter | <mm> | |
| minimum gap between parts / slot width | <mm> | |
| minimum feature (pin, rib) size | <mm> | |
| tolerance on a dimension | <+/- mm, or % of size> | |
| maximum part size | <x by y by z mm> | |
| enclosed voids | <allowed / not allowed; escape holes> | |
| file the maker accepts | <STL / STEP / 3MF; size limit> | |

## Notes

- <Anything the maker's guide adds: orientation, surface finish, inserts and their holes, ...>
