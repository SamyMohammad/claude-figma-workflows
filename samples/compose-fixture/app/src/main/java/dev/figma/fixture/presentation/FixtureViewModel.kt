package dev.figma.fixture.presentation

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class FixtureScreenId { Home, Review }
sealed interface FixtureUiState {
    val screen: FixtureScreenId
    data object Home : FixtureUiState { override val screen = FixtureScreenId.Home }
    data object Review : FixtureUiState { override val screen = FixtureScreenId.Review }
}

class FixtureViewModel : ViewModel() {
    private val mutableState = MutableStateFlow<FixtureUiState>(FixtureUiState.Home)
    val state: StateFlow<FixtureUiState> = mutableState.asStateFlow()
    fun select(screen: FixtureScreenId) {
        mutableState.value = when (screen) {
            FixtureScreenId.Home -> FixtureUiState.Home
            FixtureScreenId.Review -> FixtureUiState.Review
        }
    }
}
