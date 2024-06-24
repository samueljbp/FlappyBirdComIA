import pygame
import os
import random
import neat

ia_jogando = True
geracao = 0

LARGURA_TELA = 500
ALTURA_TELA = 800

VELOCIDADE_CANO_CHAO = 10

IMAGEM_CANO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
IMAGEM_FUNDO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
IMAGENS_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

pygame.font.init()
FONT_PONTOS = pygame.font.SysFont('arial', 50)


class Passaro:
    IMGS = IMAGENS_PASSARO
    # animações da rotação
    ROTACAO_MAXIMA = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.altura = self.y
        self.tempo = 0
        self.contagem_imagem = 0
        self.imagem = self.IMGS[0]

    def pular(self):
        self.velocidade = -10.5
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # calcular o deslocamento
        self.tempo += 1
        # formula do sorvetão
        deslocamento = 1.5 * (self.tempo ** 2) + self.velocidade * self.tempo

        # restringir o deslocamento
        if deslocamento > 16:
            deslocamento = 16
        elif deslocamento < 0:
            # incremento no deslocamento para cima para deixar a jogabilidade mais interessante
            deslocamento -= 2

        self.y += deslocamento

        # tratar o ângulo da imagem do pássaro. O or é pra que a imagem do pássaro só vire de volta pra baixo depois
        # que ele cair um pouco (50)
        if deslocamento < 0 or self.y < (self.altura + 50):
            if self.angulo < self.ROTACAO_MAXIMA:
                self.angulo = self.ROTACAO_MAXIMA
        else:
            if self.angulo > -90:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        # definir qual imagem do passaro vai usar
        self.contagem_imagem += 1

        if self.contagem_imagem < self.TEMPO_ANIMACAO:
            self.imagem = self.IMGS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 2:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 3:
            self.imagem = self.IMGS[2]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 4:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem >= self.TEMPO_ANIMACAO * 4 + 1:
            self.imagem = self.IMGS[0]
            self.contagem_imagem = 0

        # se o passaro estiver saindo, não é pra bater asa
        if self.angulo <= -80:
            self.imagem = self.IMGS[1]
            # ajuste fino pra forçar que a próxima batida de asa seja pra baixo
            self.contagem_imagem = self.TEMPO_ANIMACAO * 2

        # desenhar a imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.imagem)


class Cano:
    DISTANCIA = 200  # os canos sempre vem em 2, um embaixo e um em cima. Aqui é a distancia entre os 2
    VELOCIDADE = VELOCIDADE_CANO_CHAO

    def __init__(self, x):
        self.x = x
        self.altura = 0
        self.pos_cano_cima = 0
        self.pos_cano_baixo = 0
        self.CANO_CIMA = pygame.transform.flip(IMAGEM_CANO, False, True)
        self.CANO_BAIXO = IMAGEM_CANO
        self.passou = False  # se o cano já passou do pássaro
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(50, 450)
        self.pos_cano_cima = self.altura - self.CANO_CIMA.get_height()
        self.pos_cano_baixo = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.VELOCIDADE

    def desenhar(self, tela):
        tela.blit(self.CANO_CIMA, (self.x, self.pos_cano_cima))
        tela.blit(self.CANO_BAIXO, (self.x, self.pos_cano_baixo))

    def colidir(self, passaro):
        passaro_mask = passaro.get_mask()
        cano_cima_mask = pygame.mask.from_surface(self.CANO_CIMA)
        cano_baixo_mask = pygame.mask.from_surface(self.CANO_BAIXO)

        distancia_cano_cima = (self.x - passaro.x, self.pos_cano_cima - round(passaro.y))
        distancia_cano_baixo = (self.x - passaro.x, self.pos_cano_baixo - round(passaro.y))

        cano_baixo_ponto_colisao = passaro_mask.overlap(cano_baixo_mask, distancia_cano_baixo)
        cano_cima_ponto_colisao = passaro_mask.overlap(cano_cima_mask, distancia_cano_cima)

        return cano_baixo_ponto_colisao or cano_cima_ponto_colisao


class Chao:
    VELOCIDADE = VELOCIDADE_CANO_CHAO
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    # haverá sempre 2 imagens do chão se alternando, dado que uma imagem tem o tamanho da tela
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA

        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))


def desenhar_tela(tela, passaros, canos, chao, pontos):
    tela.blit(IMAGEM_FUNDO, (0, 0))

    for passaro in passaros:
        passaro.desenhar(tela)

    for cano in canos:
        cano.desenhar(tela)

    texto = FONT_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (LARGURA_TELA - 10 - texto.get_width(), 10))

    if ia_jogando:
        texto = FONT_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    chao.desenhar(tela)

    pygame.display.update()


# parametros que o python neat precisa receber em sua função de fitness, que no caso é a própria main
def main(genomas, config):
    global geracao
    geracao += 1

    redes = []
    lista_genomas = []
    if ia_jogando:
        passaros = []

        for _, genoma in genomas:
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            redes.append(rede)
            genoma.fitness = 0
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 350))
    else:
        passaros = [Passaro(230, 350)]

    chao = Chao(730)
    canos = [Cano(700)]
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pontos = 0
    relogio = pygame.time.Clock()

    rodando = True
    while rodando:
        relogio.tick(30)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not ia_jogando:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for passaro in passaros:
                            passaro.pular()

        indice_cano = 0
        if len(passaros) > 0:
            if (len(canos)) > 1 and passaros[0].x > (canos[0].x + canos[0].CANO_CIMA.get_width()):
                indice_cano = 1
        elif ia_jogando:
            rodando = False
            break

        if ia_jogando:
            for i, passaro in enumerate(passaros):
                passaro.mover()
                # aumentar um pouco a fitness ao andar
                lista_genomas[i].fitness += 0.1
                # nossos inputs são: altura do pássaro na tela,
                # distancia dele pro cano de cima (linear) e distancia dele pro cano de baixo (tb linear)
                output = redes[i].activate((passaro.y,
                                           abs(passaro.y - canos[indice_cano].altura),
                                           abs(passaro.y - canos[indice_cano].pos_cano_baixo)))
                # output entre -1 e 1. se o output for > 0.5, entao o passaro pula

                if output[0] > 0.5:
                    passaro.pular()

        adicionar_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(passaros):
                if cano.colidir(passaro):
                    passaros.pop(i)
                    if ia_jogando:
                        lista_genomas[i].fitness -= 1
                        lista_genomas.pop(i)
                        redes.pop(i)
                if not cano.passou and passaro.x > cano.x:
                    cano.passou = True
                    adicionar_cano = True

            cano.mover()

            if cano.x + cano.CANO_CIMA.get_width() < 0:
                remover_canos.append(cano)

        if adicionar_cano:
            pontos += 1
            canos.append(Cano(600))
            if ia_jogando:
                for genoma in lista_genomas:
                    genoma.fitness += 5

        for cano in remover_canos:
            canos.remove(cano)

        for i, passaro in enumerate(passaros):
            if passaro.y + passaro.imagem.get_height() > chao.y or passaro.y < 0:
                passaros.pop(i)
                if ia_jogando:
                    lista_genomas.pop(i)
                    redes.pop(i)

        if len(passaros) > 0 or len(canos) > 0:
            chao.mover()

        desenhar_tela(tela, passaros, canos, chao, pontos)


def rodar(caminho_config_ia):
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                caminho_config_ia)
    populacao = neat.Population(config)
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())
    if ia_jogando:
        populacao.run(main, 50)
    else:
        main(None, None)


if __name__ == '__main__':
    caminho = os.path.dirname(__file__)
    caminho_config = os.path.join(caminho, 'config.txt')
    rodar(caminho_config)
