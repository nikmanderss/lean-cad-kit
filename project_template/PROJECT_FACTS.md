# PROJECT FACTS — <PROJECT NAME>

*The one facts file. The agent reads it before it asks the client anything (`kit facts <word>` finds a line). Numbers
here are measured or given; say which, and on what.*

## 1. WHAT THE PART IS

- What it does, what it mates to, how many are made.
- Process and material: <e.g. MJF PA12 / machined 6061 / FDM PETG>; the evaluated rules are in
  `claude_code\PA12_MJF_Rules_EVALUATED.md`.

## 2. THE FRAME AND THE ORIENTATION

- Units: mm.
- The axes of the model's document frame: +X = <...>, +Y = <...>, +Z = <...> (up).
- Which end is the FRONT, and how to tell it from a picture.

## 3. THE NAMED FEATURES

| name | what it is | where (in words) | frozen? |
|---|---|---|---|
| <mounting face> | <the face that bolts to ...> | <the underside, rear half> | yes |

## 4. KEY DIMENSIONS

| what | value | measured on / given by |
|---|---|---|
| <overall envelope> | <x by y by z> | <R01_BODY_MASTER.brep, kit measure bbox> |

## 5. OPEN QUESTIONS (for the client, with a picture each)

## 6. THE CLIENT'S STANDING RULINGS — CUMULATIVE LOG (append every new ruling HERE, dated)

*Written by `kit ruling --said "<the client's words>"`, one dated line each, in the client's own words. The newest line
on a subject is the ruling. An agent's interpretation is not a ruling: `kit ruling --reading` files it under READINGS.*

## 7. FACTS ADDED AT SESSION CLOSE

*`kit close --fact "..."` appends here, at the end of the file.*
