from services.spotify_service import SpotifyService, TimeRange
from aiogram import types
from db.crud import UserManager
from db.types import TopTracksType, TopArtistsType, IUserProfile
from services.types import Track
from aiogram import Dispatcher
from localization import get_text
from typing import List, Optional

async def create_inline_result(id: str, title: str, description: str, message_text: str, reply_markup=None, thumb_url: Optional[str] = None) -> types.InlineQueryResultArticle:
    return types.InlineQueryResultArticle(
        id=id,
        title=title,
        description=description,
        input_message_content=types.InputTextMessageContent(
            message_text=message_text

        ),
        thumb_url=thumb_url,
        reply_markup=reply_markup
    )

async def get_user_top_tracks_message(user_profile: IUserProfile, user_top_tracks: Optional[List[TopTracksType]], time_period: str, language_code: str) -> str:
    if user_top_tracks is not None:
        message_template = get_text(language_code, 'tracks_inline_query_message')
        message_text = message_template.format(
            display_name=user_profile.get('display_name'),
            country=user_profile.get('country'),
            time_period=time_period
        )
        
        message_text += '\n\n' + '\n'.join([f"{i + 1}. <a href='{track.get('song_link')}'>{track.get('name')} - {track.get('artist')}</a>" for i, track in enumerate(user_top_tracks)])
    return message_text

async def get_user_top_artists_message(user_profile: IUserProfile, user_top_artists: Optional[List[TopArtistsType]], time_period: str, language_code: str) -> str:
    if user_top_artists is not None:
        message_template = get_text(language_code, 'artists_inline_query_message')
        message_text = message_template.format(
            display_name=user_profile.get('display_name'),
            country=user_profile.get('country'),
            time_period=time_period
        )
        
        message_text += '\n\n' + '\n'.join([f"{i + 1}. <a href='{track.get('artist_link')}'>{track.get('name')}</a>" for i, track in enumerate(user_top_artists)])
    return message_text

async def get_user_currently_playing_message(user_profile: IUserProfile, currently_playing: Track, language_code: str) -> str:
    if currently_playing is not None:
        message_template = get_text(language_code, 'currently_playing_inline_query_message')
        message_text = message_template.format(
            display_name=user_profile.get('display_name'),
            country=user_profile.get('country'),
            song_link=currently_playing.get('external_urls').get('spotify'),
            song=currently_playing.get('name'),
            artist=currently_playing.get('artists', [{}])[0].get('name'),
            album=currently_playing.get('album').get('name')
        )
    return message_text

async def get_user_currently_playing_description(currently_playing: Track, language_code: str) -> str:
    return get_text(language_code, 'currently_playing_inline_query_description').format(
        song=currently_playing.get('name'),
        artist=currently_playing.get('artists', [{}])[0].get('name')
        )

async def inline_handler(query: types.InlineQuery):
    user_id = query.from_user.id
    user = UserManager.get_or_create_user(user_id)
    
    results = []
    
    if user.refresh_token is None:
        results.append(
            await create_inline_result(
                id='1',
                title=get_text(user.language_code, 'none_auth_inline_query_title'),
                description=get_text(user.language_code, 'none_auth_get_stats'),
                message_text=get_text(user.language_code, 'none_auth_get_stats'),
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(
                        text=get_text(user.language_code, 'auth_button_text'),
                        url='https://t.me/SpotifyStatisticBot?start=auth'
                    )  # type: ignore
                )
            )
        )
    else:
        spotify_service = SpotifyService()
        
        currently_playing = await spotify_service.get_user_currently_playing(user_id)
        
        user_top_tracks_month = await spotify_service.get_user_top_tracks(user_id, TimeRange.SHORT_TERM)
        user_top_tracks_half_year = await spotify_service.get_user_top_tracks(user_id, TimeRange.MEDIUM_TERM)
        user_top_tracks_year = await spotify_service.get_user_top_tracks(user_id, TimeRange.LONG_TERM)
        
        user_top_artists_month = await spotify_service.get_user_top_artists(user_id, TimeRange.SHORT_TERM)
        user_top_artists_half_year = await spotify_service.get_user_top_artists(user_id, TimeRange.MEDIUM_TERM)
        user_top_artists_year = await spotify_service.get_user_top_artists(user_id, TimeRange.LONG_TERM)
        
        user_profile = await spotify_service.get_user_profile(user_id)
        
        top_tracks_month_message_text = await get_user_top_tracks_message(user_profile, user_top_tracks_month, get_text(user.language_code, 'word_month'), user.language_code)
        top_tracks_half_year_message_text = await get_user_top_tracks_message(user_profile, user_top_tracks_half_year, get_text(user.language_code, 'word_half_year'), user.language_code)
        top_tracks_year_message_text = await get_user_top_tracks_message(user_profile, user_top_tracks_year, get_text(user.language_code, 'word_year'), user.language_code)

        top_artists_month_message_text = await get_user_top_artists_message(user_profile, user_top_artists_month, get_text(user.language_code, 'word_month'), user.language_code)
        top_artists_half_year_message_text = await get_user_top_artists_message(user_profile, user_top_artists_half_year, get_text(user.language_code, 'word_half_year'), user.language_code)
        top_artists_year_message_text = await get_user_top_artists_message(user_profile, user_top_artists_year, get_text(user.language_code, 'word_year'), user.language_code)

        tracks_description_template = get_text(user.language_code, 'tracks_inline_query_description')
        artists_description_template = get_text(user.language_code, 'artists_inline_query_description')

        if currently_playing is not None:
            image_url = currently_playing.get('album').get('images', [{}])[0].get('url')
            currently_playing_message_text = await get_user_currently_playing_message(user_profile, currently_playing, user.language_code)
            currently_playing_description = await get_user_currently_playing_description(currently_playing, user.language_code)
            results.append(
                await create_inline_result(
                    id='2',
                    title=get_text(user.language_code, 'currently_playing_inline_query_title'),
                    description=currently_playing_description,
                    message_text=currently_playing_message_text,
                    thumb_url=image_url
                )
            )

        results.append(
            await create_inline_result(
                id='3',
                title=get_text(user.language_code, 'tracks_inline_query_title'),
                description=tracks_description_template.format(time_period=get_text(user.language_code, 'word_month')),
                message_text=top_tracks_month_message_text,
            )
        )
        results.append(
            await create_inline_result(
                id='4',
                title=get_text(user.language_code, 'tracks_inline_query_title'),
                description=tracks_description_template.format(time_period=get_text(user.language_code, 'word_half_year')),
                message_text=top_tracks_half_year_message_text,
            )
        )
        results.append(
            await create_inline_result(
                id='5',
                title=get_text(user.language_code, 'tracks_inline_query_title'),
                description=tracks_description_template.format(time_period=get_text(user.language_code, 'word_year')),
                message_text=top_tracks_year_message_text,
            )
        )
        
        results.append(
            await create_inline_result(
                id='6',
                title=get_text(user.language_code, 'artists_inline_query_title'),
                description=artists_description_template.format(time_period=get_text(user.language_code, 'word_month')),
                message_text=top_artists_month_message_text,
            )
        )
        results.append(
            await create_inline_result(
                id='7',
                title=get_text(user.language_code, 'artists_inline_query_title'),
                description=artists_description_template.format(time_period=get_text(user.language_code, 'word_half_year')),
                message_text=top_artists_half_year_message_text,
            )
        )
        results.append(
            await create_inline_result(
                id='8',
                title=get_text(user.language_code, 'artists_inline_query_title'),
                description=artists_description_template.format(time_period=get_text(user.language_code, 'word_year')),
                message_text=top_artists_year_message_text,
            )
        )

    await query.answer(results, cache_time=1, is_personal=True)

def register_inline(dp: Dispatcher):
    dp.register_inline_handler(inline_handler)
