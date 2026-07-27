# Asset Credits

Every file in this directory was created by **Kenney** (<https://kenney.nl>) and
released under [Creative Commons Zero v1.0 Universal (CC0)](https://creativecommons.org/publicdomain/zero/1.0/),
which places it in the public domain — free for personal and commercial use, with
attribution appreciated but not required.

Re-download and re-slice everything with `python fetch_assets.py --force`.

## Sprites

All PNGs are 64×64 tiles cut from the single tilesheet in Kenney's
[Tower Defense (top-down)](https://kenney.nl/assets/tower-defense-top-down) pack
(`Tilesheet/towerDefense_tilesheet.png`). The sheet is 23 tiles wide, so a tile's
flat index maps to row `index // 23`, column `index % 23`.

| File                 | Tile | What it is                                     |
| :------------------- | ---: | :--------------------------------------------- |
| `tile_grass.png`     |  157 | Buildable ground                               |
| `tile_dirt.png`      |  158 | The road enemies walk                          |
| `plot_open.png`      |   41 | Build plot marker                              |
| `base_stone.png`     |   84 | Pedestal drawn under every built tower         |
| `turret_cannon.png`  |  203 | Gun Turret head                                |
| `turret_frost.png`   |  227 | Frost Tower head (tinted icy blue at run time) |
| `turret_mortar.png`  |  206 | Mortar head                                    |
| `turret_gatling.png` |  226 | Gatling head                                   |
| `turret_flak.png`    |  205 | Flak Battery head                              |
| `enemy_grunt.png`    |  245 | Grunt                                          |
| `enemy_runner.png`   |  246 | Runner                                         |
| `enemy_armoured.png` |  247 | Armoured Car                                   |
| `enemy_boss.png`     |  250 | Juggernaut                                     |
| `enemy_flyer.png`    |  271 | Bomber                                         |
| `bullet.png`         |  272 | Default projectile                             |
| `shell.png`          |  275 | Mortar shell                                   |
| `frost_bolt.png`     |  273 | Frost projectile                               |
| `rocket.png`         |  251 | Flak round                                     |
| `explosion.png`      |  296 | Impact puff                                    |
| `tree.png`           |  130 | Scenery                                        |
| `bush.png`           |  131 | Scenery                                        |
| `rock.png`           |  136 | Scenery                                        |

The turret heads all point straight up in the source art, which is why the
renderer can simply rotate them toward their target.

## Fonts

| File                     | Source pack                                           | Original path                  |
| :----------------------- | :---------------------------------------------------- | :----------------------------- |
| `kenney_future.ttf`      | [Kenney Fonts](https://kenney.nl/assets/kenney-fonts) | `Fonts/Kenney Future.ttf`      |
| `kenney_mini_square.ttf` | [Kenney Fonts](https://kenney.nl/assets/kenney-fonts) | `Fonts/Kenney Mini Square.ttf` |

## Sound

| File                | Source pack                                                   | Original path                   |
| :------------------ | :------------------------------------------------------------ | :------------------------------ |
| `sfx_shoot.ogg`     | [Sci-Fi Sounds](https://kenney.nl/assets/sci-fi-sounds)       | `Audio/laserSmall_001.ogg`      |
| `sfx_explosion.ogg` | [Sci-Fi Sounds](https://kenney.nl/assets/sci-fi-sounds)       | `Audio/explosionCrunch_000.ogg` |
| `sfx_build.ogg`     | [UI Audio](https://kenney.nl/assets/ui-audio)                 | `Audio/click1.ogg`              |
| `sfx_upgrade.ogg`   | [UI Audio](https://kenney.nl/assets/ui-audio)                 | `Audio/switch2.ogg`             |
| `sfx_leak.ogg`      | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | `Audio/error_006.ogg`           |
| `sfx_wave.ogg`      | [Interface Sounds](https://kenney.nl/assets/interface-sounds) | `Audio/confirmation_002.ogg`    |

The `LICENSE-kenney-*.txt` files are the licence notices shipped inside the
original packs, copied here verbatim.
