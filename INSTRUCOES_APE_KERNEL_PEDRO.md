# INSTRUÇÕES PARA O AGENTE DE IA NA MÁQUINA VIRTUAL
# Atividade: APE - Criar uma Chamada de Sistema Personalizada no Linux (Sistemas Operacionais - UFG)

> **Destinatário:** Agente de IA executando no ambiente da Máquina Virtual (Ubuntu).  
> **Objetivo:** Executar, orientar e implementar a adição de uma chamada de sistema (syscall) personalizada no Kernel Linux, recompilar o kernel, instalá-lo e demonstrar seu funcionamento com um programa de teste em C.

---

## 1. DADOS DO ESTUDANTE E DA ATIVIDADE

* **Estudante:** Pedro Ferreira Galvao Neto
* **Disciplina:** Sistemas Operacionais (INF0202A_BEC) - Instituto de Informática / Universidade Federal de Goiás (UFG)
* **Atividade:** APE - Atividade Não Supervisionada Extra (Prazo: 30 de setembro)
* **Versão do Kernel Alvo:** Linux Kernel estável >= 6.5 (Recomendado: **Linux 6.8.12** por ser amplamente suportado e compatível com as ferramentas atuais).
* **Exigência Obrigatória do Professor:** O nome completo do estudante (**PEDRO FERREIRA GALVAO NETO**) DEVE estar gravado e visível na execução da chamada de sistema.
* **Critério de Avaliação para NOTA MÁXIMA:** Não fazer apenas um "print" básico (`printk`). A syscall deve ser funcional, útil e criativa, transferindo dados entre o espaço de usuário (*user space*) e o espaço de núcleo (*kernel space*), manipulando estruturas de SO (como `task_struct`), mas mantendo a simplicidade e estilo de código realista de um estudante de graduação.

---

## 2. ESPECIFICAÇÃO DA CHAMADA DE SISTEMA: `sys_pedro_proc_info`

### O que a chamada faz:
Um **Inspetor de Bloco de Controle de Processo (PCB / `task_struct`)**:
1. O processo em espaço de usuário chama `syscall(NUMERO_SYSCALL, &minha_struct, flags)`.
2. No kernel, a syscall acessa o ponteiro global **`current`** (que aponta para a `task_struct` do processo chamador).
3. Coleta métricas fundamentais de Sistemas Operacionais:
   - **PID** (`current->pid`)
   - **PPID** (`current->real_parent->pid`)
   - **Nome do Processo** (`current->comm`)
   - **Prioridade e Nice** do escalonador
   - **Trocas de Contexto Voluntárias** (`current->nvcsw`) e **Involuntárias** (`current->nivcsw`)
   - **Assinatura do Autor:** Preenche o campo `author` com `"Pedro Ferreira Galvao Neto"`.
4. Grava no buffer de mensagens do kernel (`printk`) uma mensagem contendo o nome completo do estudante.
5. Utiliza a função segura do kernel **`copy_to_user()`** para retornar a estrutura preenchida para a memória do usuário.

---

## 3. ROTEIRO PASSO A PASSO PARA EXECUÇÃO NA MÁQUINA VIRTUAL

O agente na VM deve guiar ou executar os seguintes passos:

### Passo 1: Instalar Dependências de Compilação
No terminal da VM (Ubuntu), executar:
```bash
sudo apt update
sudo apt install -y build-essential libncurses-dev bison flex libssl-dev \
    libelf-dev dwarves zstd bc pkg-config wget tar
```

### Passo 2: Baixar e Extrair o Código-Fonte do Linux 6.8
```bash
mkdir -p ~/kernel_build
cd ~/kernel_build

# Baixar o kernel Linux 6.8.12 oficial
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.8.12.tar.xz

# Extrair
tar -xf linux-6.8.12.tar.xz
cd linux-6.8.12
```

---

### Passo 3: Implementar a Chamada de Sistema no Código do Kernel

#### A. Criar a estrutura e a função da Syscall
Criar o arquivo `kernel/pedro_syscall.c`:
```c
#include <linux/kernel.h>
#include <linux/syscalls.h>
#include <linux/sched.h>
#include <linux/uaccess.h>

/* Estrutura para transferir dados do processo para o espaço de usuário */
struct pedro_proc_stat {
    char author[64];
    long pid;
    long ppid;
    long priority;
    long nice;
    unsigned long nvcsw;
    unsigned long nivcsw;
    char comm[16];
};

SYSCALL_DEFINE2(pedro_proc_info, struct pedro_proc_stat __user *, user_stat, int, flags)
{
    struct pedro_proc_stat kstat;
    struct task_struct *task = current;

    if (!user_stat)
        return -EINVAL;

    /* Preenche os dados do processo atual (PCB / task_struct) */
    snprintf(kstat.author, sizeof(kstat.author), "Pedro Ferreira Galvao Neto");
    kstat.pid = (long)task->pid;
    kstat.ppid = (long)task->real_parent->pid;
    kstat.priority = (long)task->prio;
    kstat.nice = (long)PRIO_TO_NICE(task->static_prio);
    kstat.nvcsw = task->nvcsw;
    kstat.nivcsw = task->nivcsw;
    get_task_comm(kstat.comm, task);

    /* Mensagem no log do kernel com o nome completo exigido */
    printk(KERN_INFO "[PEDRO FERREIRA GALVAO NETO - Syscall]: Processo '%s' (PID %ld) inspecionado com sucesso!\n",
           kstat.comm, kstat.pid);

    /* Copia os dados do espaço de kernel para o espaço de usuário com segurança */
    if (copy_to_user(user_stat, &kstat, sizeof(struct pedro_proc_stat)))
        return -EFAULT;

    return 0;
}
```

#### B. Registrar o arquivo no Makefile do kernel
Adicionar `pedro_syscall.o` ao `kernel/Makefile`:
Na linha que começa com `obj-y += ...`, adicione no final da lista:
```makefile
obj-y += pedro_syscall.o
```

#### C. Registrar o protótipo no header `include/linux/syscalls.h`
Abra `include/linux/syscalls.h` e adicione antes do `#endif`:
```c
struct pedro_proc_stat;
asmlinkage long sys_pedro_proc_info(struct pedro_proc_stat __user *user_stat, int flags);
```

#### D. Adicionar à tabela de chamadas de sistema x86_64
Abra o arquivo `arch/x86/entry/syscalls/syscall_64.tbl`.  
Verifique o último número de syscall da lista (normalmente 461 na versão 6.8) e adicione no final:
```text
462	common	pedro_proc_info		sys_pedro_proc_info
```
*(Nota: o número `462` será usado no programa de teste em espaço de usuário).*

---

### Passo 4: Configuração Otimizada para Compilação Rápida
*(Essencial para evitar que a compilação demore mais de 2 horas ou lote o disco da VM)*

```bash
# Copiar a configuração atual do Ubuntu da VM
cp /boot/config-$(uname -r) .config

# Atualizar opções para a versão atual mantendo valores padrão
make olddefconfig

# Desativar chaves de assinatura que causam erro na compilação do Ubuntu
scripts/config --disable SYSTEM_TRUSTED_KEYS
scripts/config --disable SYSTEM_REVOCATION_KEYS

# DESATIVAR símbolos de depuração pesados (Reduz o tempo de 2h para ~15-20 min e economiza 30 GB de disco)
scripts/config --disable DEBUG_INFO
scripts/config --disable DEBUG_INFO_BTF
scripts/config --disable DEBUG_INFO_DWARF4
scripts/config --disable DEBUG_INFO_DWARF5

# Nome personalizado para o kernel (aparecerá no uname -r)
scripts/config --set-str LOCALVERSION "-pedro-custom"
```

---

### Passo 5: Compilar e Instalar o Kernel
```bash
# Compilar usando todos os núcleos da VM
make -j$(nproc)

# Instalar os módulos e a imagem do kernel
sudo make modules_install
sudo make install

# Atualizar o GRUB
sudo update-grub
```

---

### Passo 6: Reiniciar a VM no Novo Kernel
```bash
sudo reboot
```
Após reiniciar, abra o terminal e confirme:
```bash
uname -r
```
*Deverá exibir algo como:* `6.8.12-pedro-custom` (confirmando que o sistema iniciou com o seu kernel).

---

### Passo 7: Programa de Teste em C em Espaço de Usuário (`teste_pedro.c`)

Criar o arquivo `teste_pedro.c` na VM:
```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>

#define SYS_PEDRO_PROC_INFO 462

struct pedro_proc_stat {
    char author[64];
    long pid;
    long ppid;
    long priority;
    long nice;
    unsigned long nvcsw;
    unsigned long nivcsw;
    char comm[16];
};

int main() {
    struct pedro_proc_stat stat;
    long ret;

    printf("============================================================\n");
    printf(" TESTE DA CHAMADA DE SISTEMA PERSONALIZADA NO LINUX         \n");
    printf(" Aluno: Pedro Ferreira Galvao Neto - Sistemas Operacionais  \n");
    printf("============================================================\n\n");

    printf("[*] Invocando syscall %d...\n", SYS_PEDRO_PROC_INFO);
    ret = syscall(SYS_PEDRO_PROC_INFO, &stat, 0);

    if (ret != 0) {
        perror("[-] Falha ao executar syscall");
        return 1;
    }

    printf("[+] Syscall executada com sucesso pelo kernel!\n\n");
    printf("--- DADOS EXTRAIDOS DO BLOCO DE CONTROLE DO PROCESSO (PCB) ---\n");
    printf("  Autor da Syscall               : %s\n", stat.author);
    printf("  Comando / Processo             : %s\n", stat.comm);
    printf("  PID (Process ID)               : %ld\n", stat.pid);
    printf("  PPID (Parent Process ID)       : %ld\n", stat.ppid);
    printf("  Prioridade no Kernel           : %ld\n", stat.priority);
    printf("  Valor Nice                     : %ld\n", stat.nice);
    printf("  Trocas de Contexto Voluntarias : %lu\n", stat.nvcsw);
    printf("  Trocas de Contexto Involuntarias: %lu\n", stat.nivcsw);
    printf("---------------------------------------------------------------\n\n");

    printf("[*] Verificando se foi registrado no buffer de log do kernel:\n");
    printf("    Execute: sudo dmesg | grep 'PEDRO FERREIRA GALVAO NETO'\n");

    return 0;
}
```

Compilar e executar:
```bash
gcc teste_pedro.c -o teste_pedro
./teste_pedro
sudo dmesg | tail -n 10
```

---

## 4. ROTEIRO PARA A GRAVAÇÃO DO VÍDEO (REQUISITO DA DISCIPLINA)

1. **Estrutura do vídeo:**
   - Usar ferramenta como SimpleScreenRecorder, OBS Studio ou Kazam com webcam ativada no canto da tela (o professor exige que o rosto e a voz apareçam).
   - Duração recomendada: 3 a 5 minutos.
2. **Falas recomendadas:**
   - **Apresentação:** "Olá professor, sou o aluno Pedro Ferreira Galvao Neto da disciplina de Sistemas Operacionais. Esta é a demonstração da Atividade Não Supervisionada Extra (APE)."
   - **Comprovação do Kernel:** Executar `uname -r` no terminal e mostrar o kernel modificado (`6.8.12-pedro-custom`).
   - **Apresentação do Código:** Mostrar rapidamente o trecho no arquivo `pedro_syscall.c` (destacando o acesso à `task_struct`, o uso de `copy_to_user` e o `printk` com o nome) e o registro no `syscall_64.tbl`.
   - **Execução:** Compilar e rodar `./teste_pedro`, mostrando a tabela com os dados reais do PCB e o nome completo.
   - **Log do Kernel:** Rodar `sudo dmesg | tail -n 5` mostrando a mensagem gravada diretamente no kernel log.
