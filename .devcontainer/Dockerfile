# Base Image
FROM node:20-bullseye

ARG TZ
ENV TZ=${TZ}

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
  && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    fzf \
    gh \
    git \
    jq \
    locales \
    nano \
    sudo \
    vim \
    zsh \
  && rm -rf /var/lib/apt/lists/*

RUN sed -i '/ko_KR.UTF-8/s/^# //g' /etc/locale.gen \
  && locale-gen ko_KR.UTF-8

ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

WORKDIR /workspace

# 여기서는 아직 root
RUN npm install -g @anthropic-ai/claude-code

ENV SHELL=/bin/zsh

# 마지막에만 node 사용자로 전환
USER node
