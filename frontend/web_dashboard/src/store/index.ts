/* eslint-disable @typescript-eslint/no-explicit-any */
import { configureStore } from '@reduxjs/toolkit';
import { persistStore } from 'redux-persist';

// Slices
import forensicsReducer from './slices/forensicsSlice';
import vocalsocReducer from './slices/vocalsocSlice'

const rootReducer = {
  forensics: forensicsReducer,
  vocalsoc: vocalsocReducer,
  // auth: authReducer,
  // pasm: pasmReducer,
  // ui: uiReducer,
};

// Cast the reducers collection to `any` to avoid strict RootState typing across
// partially implemented slices while we progressively add them. This keeps
// existing hooks compiling until their slices are added.
export const store = configureStore({

  reducer: rootReducer as any,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export const persistor = persistStore(store);

export type RootState = any;
export type AppDispatch = typeof store.dispatch;

export default store;
