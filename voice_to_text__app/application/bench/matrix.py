from voice_to_text__app.domain.models import TranscribeConfig
from voice_to_text__app.infrastructure.config.settings import Settings


def iter_matrix(base_cfg: TranscribeConfig, *, settings: Settings):
    """
    Генератор конфигов для бенча.
    Берём базовый cfg (из settings.whisper) и варьируем поля по settings.bench матрице.
    """
    b = settings.bench

    for compute in b.computes:
        for thr in b.threads:
            for wrk in b.workers:
                for beam in b.beams:
                    for pat in b.patiences:
                        for vad in b.vads:
                            yield base_cfg.model_copy(
                                update={
                                    "device": "cpu",
                                    "compute_type": compute,
                                    "threads": thr,
                                    "workers": wrk,
                                    "beam_size": beam,
                                    "patience": pat,
                                    "vad": vad,
                                }
                            )