<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/header-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/header-light.svg">
  <img alt="Oleg Rune — embedded · firmware · STM32" src="assets/header-light.svg" width="100%">
</picture>

</div>

<br>

```c
/* oleg.c */
#include "stm32.h"

const engineer_t oleg = {
    .name  = "Oleg Rune",
    .focus = "embedded / firmware",
    .stack = { "C", "C++", "STM32 HAL", "Arm Cortex-M" },
    .motto = "quiet code for small machines",
};

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    while (1) {
        read_datasheet();
        write_firmware();
        HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);  /* never gets old */
    }
}
```

<!--
<p align="center">
  <a href="https://t.me/USERNAME"><img src="https://img.shields.io/badge/telegram-111?style=flat-square&logo=telegram&logoColor=white" alt="telegram"></a>
  <a href="https://www.linkedin.com/in/USERNAME"><img src="https://img.shields.io/badge/linkedin-111?style=flat-square&logo=linkedin&logoColor=white" alt="linkedin"></a>
  <a href="mailto:EMAIL"><img src="https://img.shields.io/badge/email-111?style=flat-square&logo=maildotru&logoColor=white" alt="email"></a>
</p>
-->

<br>

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/footer-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/footer-light.svg">
  <img alt="" src="assets/footer-light.svg" width="100%">
</picture>

<sub>鯉の滝登り — the carp that climbs the waterfall becomes a dragon</sub>

</div>
